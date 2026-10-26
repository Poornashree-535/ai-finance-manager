"""Turn messy bank descriptions into short, comparable text.

"UPI/SWIGGY/4839201/Payment" -> "swiggy"
"""
import re

NOISE = {
    "upi", "pos", "neft", "imps", "rtgs", "ach", "payment", "paid", "pay", "to",
    "from", "ref", "txn", "transfer", "debit", "card", "purchase", "via", "wdl",
    "mob", "mobile", "banking", "phonepe", "gpay", "googlepay", "in", "com",
}


def _upi_payee(text: str):
    """HDFC-style 'UPI-PAYEE NAME-vpa@bank-IFSC-ref' (or UPI/PAYEE/ref) -> 'payee name'."""
    m = re.match(r"\s*upi\s*[-/]\s*([^-/@]+)(?=[-/])", text)
    return m.group(1) if m else None


def clean_description(text: str) -> str:
    text = str(text).lower()
    payee = _upi_payee(text)
    if payee:
        text = payee
    text = re.sub(r"[\w.\-]+@[\w.]+", " ", text)   # UPI handles like name@okaxis
    text = re.sub(r"[^a-z\s]", " ", text)          # digits, slashes, symbols
    tokens = [t for t in text.split() if t not in NOISE and len(t) > 1]
    return " ".join(tokens)
