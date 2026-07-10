"""Run the agent on four showcase questions and save each decision log."""

import os
import sys
import time

from agent import answer_question

QUESTIONS = [
    "How many households and how much total revenue are in this data?",
    "Do households that received marketing campaigns spend more on average than those that didn't?",
    "Which income bracket has the highest coupon redemption rate, and how big is each bracket?",
    "What are the top 5 product departments by total sales value?",
]

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    sys.exit("Set GEMINI_API_KEY first (free key: https://aistudio.google.com)")

os.makedirs("outputs", exist_ok=True)

for i, q in enumerate(QUESTIONS, 1):
    print(f"\n{'=' * 60}\nDEMO {i}/4: {q}\n{'=' * 60}")
    answer, log_md = answer_question(q, api_key)
    print(f"\nANSWER:\n{answer}\n")
    with open(f"outputs/demo_{i}.md", "w") as f:
        f.write(log_md)
    print(f"Saved outputs/demo_{i}.md")
    time.sleep(30)  # stay well inside the free tier's per-minute limits

print("\nAll demos complete.")