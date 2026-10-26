"""Merchant matching + categorization.

Order of checks (first hit wins):
1. Rules the user taught us earlier (data/user_rules.json)
2. Exact merchant keyword in MERCHANT_MAP
3. Fuzzy match (handles typos like "swigy")
4. Otherwise -> Uncategorized (the app asks the user)
"""
import json
import re
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz, process

from .cleaning import clean_description
from .config import (FUZZY_CUTOFF, MERCHANT_MAP, REVIEW_THRESHOLD, UNCATEGORIZED)

RULES_PATH = Path(__file__).resolve().parent.parent / "data" / "user_rules.json"
_KEYS_LONGEST_FIRST = sorted(MERCHANT_MAP, key=len, reverse=True)


def load_user_rules(path: Path = RULES_PATH) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def save_user_rules(rules: dict, path: Path = RULES_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rules, indent=2))


def match_merchant(clean: str, user_rules: dict | None = None):
    """Return (merchant, category, confidence)."""
    if user_rules and clean in user_rules:
        return clean, user_rules[clean], 1.0

    for key in _KEYS_LONGEST_FIRST:  # longest first so "swiggy instamart" beats "swiggy"
        if re.search(rf"\b{re.escape(key)}\b", clean):
            return key, MERCHANT_MAP[key], 1.0

    best = None
    for token in clean.split():
        if len(token) < 4:
            continue
        hit = process.extractOne(token, list(MERCHANT_MAP), scorer=fuzz.ratio,
                                 score_cutoff=FUZZY_CUTOFF)
        if hit and (best is None or hit[1] > best[1]):
            best = hit
    if best:
        key, score, _ = best
        return key, MERCHANT_MAP[key], score / 100

    return None, UNCATEGORIZED, 0.0


def categorize(df: pd.DataFrame, user_rules: dict | None = None) -> pd.DataFrame:
    df = df.copy()
    df["clean_description"] = df["description"].map(clean_description)
    results = [match_merchant(c, user_rules) for c in df["clean_description"]]
    df["merchant"] = [r[0] for r in results]
    df["category"] = [r[1] for r in results]
    df["confidence"] = [r[2] for r in results]
    df["needs_review"] = df["confidence"] < REVIEW_THRESHOLD
    return df
