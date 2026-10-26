"""Streamlit app. Run with:  streamlit run app.py"""
from pathlib import Path

import plotly.express as px
import streamlit as st

from src.analytics import generate_insights, summarize
from src.categorizer import categorize, load_user_rules, save_user_rules
from src.config import CATEGORIES, UNCATEGORIZED
from src.ingestion import load_statement

SAMPLE = Path(__file__).parent / "data" / "sample_statement.csv"

st.set_page_config(page_title="Finance AI", page_icon="💰", layout="wide")
st.title("💰 AI-Powered Personal Finance Manager")
st.caption("Upload a bank statement (CSV or Excel). Your data stays on your machine.")

# ---------- 1. Upload ----------
uploaded = st.sidebar.file_uploader("Bank statement", type=["csv", "xlsx", "xls"])
use_sample = st.sidebar.checkbox("Use sample statement")

if uploaded:
    source, key = uploaded, uploaded.name
elif use_sample:
    source, key = SAMPLE, "sample"
else:
    st.info("Upload a statement in the sidebar, or tick **Use sample statement** to try it out.")
    st.stop()

if st.session_state.get("source_key") != key:
    try:
        raw = load_statement(source)
    except ValueError as err:
        st.error(str(err))
        st.stop()
    expenses = raw[raw["type"] == "debit"].reset_index(drop=True)
    st.session_state.source_key = key
    st.session_state.income = raw.loc[raw["type"] == "credit", "amount"].sum()
    st.session_state.df = categorize(expenses, load_user_rules())

df = st.session_state.df

# ---------- 2. Ask the user about unclear transactions ----------
# Same payee = one question (answering "Rahul" once fixes all his transactions).
df["review_key"] = df["clean_description"].where(df["clean_description"] != "", df["description"])
pending = df[df["needs_review"]]
if not pending.empty:
    groups = (pending.groupby("review_key")
              .agg(example=("description", "first"), transactions=("amount", "size"),
                   total=("amount", "sum"), category=("category", "first"))
              .reset_index())
    st.subheader(f"🤔 {len(groups)} payee(s) need your help ({len(pending)} transactions)")
    st.write("Pick a category for each payee. I'll remember your choices for next time.")
    edited = st.data_editor(
        groups,
        column_config={
            "review_key": st.column_config.TextColumn("Payee"),
            "example": st.column_config.TextColumn("Example from statement"),
            "total": st.column_config.NumberColumn("Total ₹", format="%.2f"),
            "category": st.column_config.SelectboxColumn(
                "Category", options=[UNCATEGORIZED] + CATEGORIES, required=True),
        },
        disabled=["review_key", "example", "transactions", "total"],
        hide_index=True,
        key=f"editor_{key}",
    )
    b1, b2, _ = st.columns([1, 1.4, 3])
    if b1.button("Confirm categories", type="primary"):
        rules = load_user_rules()
        for _, row in edited.iterrows():
            if row["category"] == UNCATEGORIZED:
                continue
            mask = df["review_key"] == row["review_key"]
            df.loc[mask, "category"] = row["category"]
            df.loc[mask, "needs_review"] = False
            clean = df.loc[mask, "clean_description"].iloc[0]
            if clean:
                rules[clean] = row["category"]
        save_user_rules(rules)
        st.session_state.df = df
        st.rerun()
    if b2.button("Put the rest in Miscellaneous"):
        rest = df["needs_review"] & (df["category"] == UNCATEGORIZED)
        df.loc[rest, "category"] = "Miscellaneous"
        df.loc[rest, "needs_review"] = False
        st.session_state.df = df
        st.rerun()

# ---------- 3. Dashboard ----------
st.divider()
st.subheader("📊 Spending report")
summary = summarize(df)
by_cat = summary["by_category"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total spent", f"₹{summary['total']:,.0f}")
c2.metric("Money in", f"₹{st.session_state.income:,.0f}")
c3.metric("Transactions", len(df))
c4.metric("Top category", by_cat.iloc[0]["category"] if not by_cat.empty else "-")

left, right = st.columns(2)
left.plotly_chart(px.pie(by_cat, names="category", values="amount", hole=0.45,
                         title="Spending distribution"), width="stretch")
right.plotly_chart(px.bar(by_cat, x="category", y="amount", title="Category-wise spending",
                          labels={"amount": "₹"}), width="stretch")

st.subheader("💡 Insights")
for line in generate_insights(df):
    st.markdown(f"- {line}")

st.subheader("All transactions")
choice = st.multiselect("Filter by category", sorted(df["category"].unique()))
view = df[df["category"].isin(choice)] if choice else df
st.dataframe(view[["date", "description", "amount", "category", "confidence"]],
             width="stretch")
st.download_button("Download categorized CSV",
                   view.drop(columns=["clean_description"]).to_csv(index=False),
                   "categorized_transactions.csv", "text/csv")
