"""AI Data Analyst Agent.

Takes a plain-English business question, and autonomously:
inspects the database schema -> writes SQL -> executes it ->
recovers from errors -> answers in plain English.
Every step is recorded in a decision log.

Usage:  python3 agent.py "Which income bracket redeems the most coupons?"
Needs:  export GEMINI_API_KEY="your-free-key"
"""

import json
import os
import sys
import time

import requests

from tools import get_schema, run_sql

MODEL = "gemini-2.5-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
MAX_STEPS = 10  # hard stop so the agent can never loop forever

SYSTEM_PROMPT = """You are a careful data analyst agent with READ-ONLY access to a retail SQLite database
(2,500 households, ~2.6M transactions over 2 years).

To answer the user's question:
1. ALWAYS call get_schema first to see the real tables and columns.
2. Write ONE SELECT query at a time and call run_sql (SQLite dialect).
3. If a query returns ERROR, read it carefully and fix your SQL.
4. Prefer aggregation (SUM, COUNT, AVG, GROUP BY) over fetching raw rows.
5. Households can appear multiple times in campaign/coupon tables - use DISTINCT
   when building household lists to avoid double counting.
6. When you have the numbers, STOP querying and give a final plain-English answer
   that cites the actual figures.

Notes: tables join on household_key. Most column names are UPPERCASE
(SALES_VALUE, BASKET_ID) but household_key is lowercase."""

TOOLS = [{
    "functionDeclarations": [
        {
            "name": "get_schema",
            "description": "List every table and its columns in the database.",
        },
        {
            "name": "run_sql",
            "description": "Run one read-only SELECT query and get the results (or an error to fix).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "A single SQLite SELECT query."}
                },
                "required": ["query"],
            },
        },
    ]
}]


def call_gemini(contents: list, api_key: str) -> dict:
    """One round-trip to the Gemini API."""
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "tools": TOOLS,
    }
    resp = requests.post(
        API_URL,
        params={"key": api_key},
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text[:500]}")
    return resp.json()


def execute_tool(name: str, args: dict) -> str:
    """Route a tool call from the model to the real Python function."""
    if name == "get_schema":
        return get_schema()
    if name == "run_sql":
        return run_sql(args.get("query", ""))
    return f"ERROR: unknown tool '{name}'"


def answer_question(question: str, api_key: str):
    """The agent loop. Returns (final_answer, decision_log_markdown)."""
    log = [f"# Decision Log\n\n**Question:** {question}\n"]
    contents = [{"role": "user", "parts": [{"text": question}]}]

    for step in range(1, MAX_STEPS + 1):
        data = call_gemini(contents, api_key)

        try:
            parts = data["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError):
            log.append(f"\n**Step {step}: unexpected API response**\n```\n{json.dumps(data)[:800]}\n```")
            return "The model returned an unexpected response - see the log.", "\n".join(log)

        # keep the model's turn in the conversation history
        contents.append({"role": "model", "parts": parts})

        texts = [p["text"] for p in parts if "text" in p]
        calls = [p["functionCall"] for p in parts if "functionCall" in p]

        for t in texts:
            if t.strip():
                log.append(f"\n**Step {step} - agent reasoning:** {t.strip()}")

        if not calls:  # no tool requested -> this is the final answer
            final = "\n".join(texts).strip() or "(no answer produced)"
            log.append(f"\n---\n\n## Final Answer\n\n{final}\n")
            return final, "\n".join(log)

        # execute each requested tool and feed the result back
        response_parts = []
        for fc in calls:
            name = fc.get("name", "")
            args = fc.get("args", {}) or {}
            log.append(f"\n**Step {step} - tool call:** `{name}` "
                       + (f"\n```sql\n{args.get('query')}\n```" if "query" in args else ""))
            result = execute_tool(name, args)
            shown = result if len(result) <= 1200 else result[:1200] + "\n...(truncated in log)"
            log.append(f"**Result:**\n```\n{shown}\n```")
            response_parts.append({
                "functionResponse": {"name": name, "response": {"result": result}}
            })
        contents.append({"role": "user", "parts": response_parts})

    log.append("\n**Stopped: reached max steps.**")
    return "The agent hit its step limit before finishing - see the log.", "\n".join(log)


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("No GEMINI_API_KEY set.\nGet a free key at https://aistudio.google.com "
                 "then run:  export GEMINI_API_KEY=\"your-key\"")

    question = " ".join(sys.argv[1:]).strip() or input("Ask a business question: ").strip()
    print(f"\nQUESTION: {question}\n" + "=" * 60)

    answer, log_md = answer_question(question, api_key)

    print("\n" + "=" * 60 + f"\nANSWER:\n{answer}\n")

    os.makedirs("outputs", exist_ok=True)
    fname = f"outputs/log_{time.strftime('%Y%m%d_%H%M%S')}.md"
    with open(fname, "w") as f:
        f.write(log_md)
    print(f"Decision log saved to {fname}")


if __name__ == "__main__":
    main()