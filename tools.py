"""Tools the agent can call. Both are strictly read-only."""

import os
import sqlite3

# Use the full database locally; fall back to the demo DB in the cloud.
DB_PATH = "ecommerce.db" if os.path.exists("ecommerce.db") else "ecommerce_demo.db"
MAX_ROWS = 50  # never flood the model with huge results


def get_schema() -> str:
    """Return every table and its columns so the agent can orient itself."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)  # read-only connection
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    lines = []
    for t in tables:
        cur.execute(f"PRAGMA table_info({t})")
        cols = ", ".join(f"{c[1]} ({c[2]})" for c in cur.fetchall())
        lines.append(f"TABLE {t}: {cols}")
    conn.close()
    return "\n".join(lines)


def run_sql(query: str) -> str:
    """Execute one SELECT query with guardrails; return results or the error."""
    q = query.strip().rstrip(";").strip()
    lowered = q.lower()

    # GUARDRAIL 1: read-only queries only
    if not (lowered.startswith("select") or lowered.startswith("with")):
        return "ERROR: Only SELECT queries are allowed (read-only guardrail)."
    # GUARDRAIL 2: one statement only (blocks injection-style chaining)
    if ";" in q:
        return "ERROR: Multiple SQL statements are not allowed."

    try:
        # GUARDRAIL 3: the connection itself is opened read-only
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute(q)
        rows = cur.fetchmany(MAX_ROWS + 1)
        headers = [d[0] for d in cur.description] if cur.description else []
        conn.close()
    except Exception as e:
        return f"ERROR: {e}"  # the agent reads this and fixes its own SQL

    truncated = len(rows) > MAX_ROWS
    rows = rows[:MAX_ROWS]
    out = [" | ".join(headers)]
    for r in rows:
        out.append(" | ".join(str(v) for v in r))
    if not rows:
        out.append("(no rows returned)")
    if truncated:
        out.append(f"... (truncated to first {MAX_ROWS} rows)")
    return "\n".join(out)