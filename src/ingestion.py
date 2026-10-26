"""Load a bank statement (CSV/Excel) and normalize it to one schema:
date | description | amount | type ("debit" or "credit")
"""
import pandas as pd

COLUMN_ALIASES = {
    "date": ["date", "txn date", "transaction date", "value date", "tran date"],
    "description": ["description", "narration", "particulars", "details",
                    "transaction details", "remarks"],
    "debit": ["debit", "withdrawal", "withdrawals", "withdrawal amt.", "debit amount", "dr"],
    "credit": ["credit", "deposit", "deposits", "deposit amt.", "credit amount", "cr"],
    "amount": ["amount", "transaction amount"],
}


def _find_column(columns: dict, key: str):
    for name in COLUMN_ALIASES[key]:
        if name in columns:
            return columns[name]
    return None


def _to_number(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.replace(r"[₹,\s]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce").fillna(0.0)


def _read_raw(file) -> pd.DataFrame:
    """Read the file with no header assumptions (banks add account details on top)."""
    name = getattr(file, "name", str(file)).lower()
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file, header=None, dtype=str)
    return pd.read_csv(file, header=None, dtype=str, names=range(40), sep=",",
                       engine="python", skip_blank_lines=False)


def _find_header_row(raw: pd.DataFrame):
    """Index of the first row that looks like a column header, else None."""
    known = lambda key: set(COLUMN_ALIASES[key])
    for i in range(min(len(raw), 60)):
        cells = {str(v).strip().lower() for v in raw.iloc[i] if pd.notna(v)}
        has_money = cells & (known("debit") | known("credit") | known("amount"))
        if cells & known("date") and cells & known("description") and has_money:
            return i
    return None


def _parse_dates(series: pd.Series) -> pd.Series:
    """Try the common bank date formats, then fall back to a day-first guess."""
    text = series.astype(str).str.strip().str.slice(0, 10)
    for fmt in ("%d/%m/%y", "%d/%m/%Y", "%d-%m-%Y", "%d-%m-%y", "%Y-%m-%d"):
        parsed = pd.to_datetime(text, format=fmt, errors="coerce")
        if parsed.notna().sum() >= max(1, int(0.5 * series.notna().sum())):
            return parsed
    return pd.to_datetime(series, dayfirst=True, errors="coerce")


def load_statement(file) -> pd.DataFrame:
    """`file` can be a path or a Streamlit UploadedFile."""
    table = _read_raw(file)
    header_row = _find_header_row(table)
    if header_row is None:
        raise ValueError(
            "Could not find the transaction table. I look for a header row containing a "
            "Date column, a Description/Narration column and Debit/Credit (or Amount) columns."
        )
    raw = table.iloc[header_row + 1:].copy()
    raw.columns = [str(v).strip() if pd.notna(v) else f"col{j}"
                   for j, v in enumerate(table.iloc[header_row])]
    raw = raw.dropna(axis=1, how="all").reset_index(drop=True)

    columns = {str(c).strip().lower(): c for c in raw.columns}
    date_col = _find_column(columns, "date")
    desc_col = _find_column(columns, "description")
    debit_col = _find_column(columns, "debit")
    credit_col = _find_column(columns, "credit")
    amount_col = _find_column(columns, "amount")
    zeros = pd.Series(0.0, index=raw.index)

    if debit_col or credit_col:
        debit = _to_number(raw[debit_col]) if debit_col else zeros
        credit = _to_number(raw[credit_col]) if credit_col else zeros
    else:  # single column: negative = money out
        amount = _to_number(raw[amount_col])
        debit, credit = (-amount).clip(lower=0), amount.clip(lower=0)

    df = pd.DataFrame({
        "date": _parse_dates(raw[date_col]),
        "description": raw[desc_col].astype(str).str.strip(),
        "debit": debit,
        "credit": credit,
    }).dropna(subset=["date"])  # drops the ****** divider row and footer/summary rows

    df["amount"] = df["debit"].where(df["debit"] > 0, df["credit"])
    df["type"] = df["debit"].gt(0).map({True: "debit", False: "credit"})
    df = df[df["amount"] > 0]
    return df[["date", "description", "amount", "type"]].reset_index(drop=True)
