"""Streamlit front end for the AI Data Analyst Agent."""

import os
import streamlit as st

from agent import answer_question

st.set_page_config(page_title="AI Data Analyst Agent", page_icon="📊", layout="centered")

st.title("📊 AI Data Analyst Agent")
st.markdown(
    "Ask a business question in plain English. The agent inspects the database schema, "
    "writes its own SQL, runs it against **2.6 million retail transactions**, and explains the answer."
)

# API key: from environment, or let the user paste one in the sidebar
api_key = os.environ.get("GEMINI_API_KEY")
with st.sidebar:
    st.header("Setup")
    if api_key:
        st.success("API key loaded from environment.")
    else:
        api_key = st.text_input("Gemini API key", type="password",
                                help="Get a free key at aistudio.google.com")
    st.markdown("---")
    st.caption("Read-only database access. The agent can only run SELECT queries.")

# Example questions users can click
st.markdown("**Try an example:**")
examples = [
    "How many households and how much total revenue are in this data?",
    "Do households that received marketing campaigns spend more on average?",
    "Which income bracket has the highest coupon redemption rate?",
    "What are the top 5 product departments by total sales value?",
]
cols = st.columns(2)
clicked = None
for i, ex in enumerate(examples):
    if cols[i % 2].button(ex, use_container_width=True):
        clicked = ex

question = st.text_input("Your question:", value=clicked or "")

if st.button("Ask the agent", type="primary") or clicked:
    q = question or clicked
    if not api_key:
        st.error("Please provide a Gemini API key in the sidebar.")
    elif not q:
        st.warning("Type a question or click an example above.")
    else:
        with st.spinner("The agent is thinking — inspecting schema, writing SQL, querying..."):
            try:
                answer, log_md = answer_question(q, api_key)
                st.markdown("### Answer")
                st.markdown(answer)
                with st.expander("See the agent's decision log (schema → SQL → result)"):
                    st.markdown(log_md)
            except Exception as e:
                st.error(f"Something went wrong: {e}")