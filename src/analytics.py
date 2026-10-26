"""Spending summary and simple rule-based insights."""
import pandas as pd

from .config import UNCATEGORIZED


def summarize(df: pd.DataFrame) -> dict:
    total = df["amount"].sum()
    by_category = (df.groupby("category", as_index=False)["amount"].sum()
                   .sort_values("amount", ascending=False))
    by_category["share"] = by_category["amount"] / total * 100 if total else 0.0
    top = df.nlargest(5, "amount")[["date", "description", "amount", "category"]]
    return {"total": total, "by_category": by_category, "top_transactions": top}


def generate_insights(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return []
    s = summarize(df)
    insights = []

    known = s["by_category"][s["by_category"]["category"] != UNCATEGORIZED]
    if not known.empty:
        top = known.iloc[0]
        insights.append(f"**{top['category']}** is your biggest expense: "
                        f"₹{top['amount']:,.0f} ({top['share']:.0f}% of total spending).")

    largest = df.loc[df["amount"].idxmax()]
    insights.append(f"Your largest single transaction was ₹{largest['amount']:,.0f} "
                    f"on {largest['date']:%d %b} ({largest['description'][:40]}).")

    days = (df["date"].max() - df["date"].min()).days + 1
    insights.append(f"You spent about ₹{s['total'] / days:,.0f} per day on average "
                    f"across {len(df)} transactions.")

    pending = int((df["category"] == UNCATEGORIZED).sum())
    if pending:
        insights.append(f"{pending} transaction(s) are still uncategorized, "
                        "so the numbers above may shift once you classify them.")
    return insights
