# AI Data Analyst Agent

An autonomous agent that answers plain-English business questions about a database by inspecting its schema, writing and running its own SQL, recovering from its own errors, and explaining the results — with a full decision log of its reasoning.

Ask it *"Do households that received marketing campaigns spend more?"* and it figures out the tables, writes the query, runs it against 2.6 million rows, and answers: *"Yes — roughly 4.4x more ($4,491.99 vs $1,028.54)."*

## Live Web App

A Streamlit front end lets you ask questions and watch the agent work — schema inspection, the SQL it wrote, and the answer, all in the browser.

**[▶ Try it live →](https://ashranawork-ai-agent.streamlit.app)**

Run it locally:

​```bash
pip3 install -r requirements.txt
export GEMINI_API_KEY="your-free-key"
python3 -m streamlit run app.py
​```

## Why this exists (and why not just paste data into ChatGPT?)

A chatbot can discuss data you paste into it. This agent solves the problems a chatbot can't:

- **Scale.** The database is 129MB / 2.6M rows — far too large to paste into any LLM's context window. The agent never sends the data to the model; it sends the *schema*, lets the model write SQL, runs that SQL locally, and returns only the small result.
- **Accuracy.** LLMs approximate arithmetic over large inputs. This agent runs real SQL, so every number is exact and verifiable.
- **Auditability.** The decision log records the exact SQL executed, so a human can verify the result. "Here's the query" beats "trust me."
- **Safety.** Read-only connection, SELECT-only validation, single-statement enforcement, and a hard step limit — so it's safe to point at a real database.

## What it does

1. **Inspects the schema** — reads the real tables and columns at runtime (so it works on *any* SQLite database, not just this one).
2. **Writes SQL** — generates a SQLite query to answer the question.
3. **Executes and self-corrects** — runs the query read-only; if it errors, the agent reads the error and rewrites the SQL.
4. **Answers in plain English** — cites the actual figures.
5. **Logs every step** — a full decision log of reasoning, queries, and results.

## Architecture

Built from scratch (no agent framework) to demonstrate the core pattern:

```
User question
     │
     ▼
┌─────────────┐   requests a tool    ┌──────────────┐
│   Gemini    │ ───────────────────▶ │  Agent loop  │
│    (LLM)    │ ◀─────────────────── │   (Python)   │
└─────────────┘   returns result     └──────┬───────┘
                                            │ calls
                                    ┌───────▼────────┐
                                    │  Tools:        │
                                    │  get_schema    │
                                    │  run_sql (RO)  │
                                    └───────┬────────┘
                                            │
                                    ┌───────▼────────┐
                                    │  SQLite DB     │
                                    │  (2.6M rows)   │
                                    └────────────────┘
```

The model is given two tools and loops: it requests a tool, the Python layer executes it and feeds back the result, and the model decides what to do next — until it has enough to answer.

## Example (real decision log)

**Question:** *How many households are in this data?*

1. Agent calls `get_schema` → sees 7 tables
2. Agent writes: `SELECT COUNT(DISTINCT household_key) ...` (using UNION across tables to be thorough)
3. Runs it → `2500`
4. Answers: *"2,500 unique households; 801 have demographic profiles."*

Full logs for four sample questions are in [`outputs/`](outputs/).

## Guardrails

- **Read-only database connection** (opened with `mode=ro`)
- **SELECT/WITH only** — write queries are rejected before execution
- **Single statement only** — blocks chained/injection-style queries
- **Row cap** — results truncated so the model isn't flooded
- **Max step limit** — the loop can never run forever
- **Retry with backoff** — survives transient API errors (429/503)

## Tech Stack

- **Python** — the agent loop, built without a framework
- **Google Gemini API** — the reasoning model (tool calling)
- **SQLite** — the queryable database

## How to Run

```bash
pip3 install -r requirements.txt
export GEMINI_API_KEY="your-free-key"   # from https://aistudio.google.com
python3 agent.py "How many households are in this data?"
```

Point it at any SQLite database by replacing `ecommerce.db` (the schema is read at runtime, so no code changes are needed).

## Limitations & What I'd Improve

- **No analytical caveats.** The agent reports figures accurately but doesn't volunteer judgment like selection bias (e.g. campaign-targeted households may already be high spenders). A human analyst still adds that layer.
- **SQLite-only.** Tuned for SQLite dialect; supporting Postgres/MySQL would need dialect handling.
- **Free-tier rate limits** shape how fast batch questions can run (hence the backoff logic).
- **No result validation.** The agent trusts its own SQL; a production version would add sanity checks on returned values.
- **Next step:** a web front end (Streamlit) so the agent's reasoning streams live in a browser — far more accessible than the terminal.

## Note on Data

The database is built from the public Dunnhumby "Complete Journey" dataset and is not included in this repository due to size. The agent works with any SQLite database.
