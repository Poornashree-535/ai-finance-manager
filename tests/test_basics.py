from pathlib import Path

from src.categorizer import categorize, match_merchant
from src.cleaning import clean_description
from src.ingestion import load_statement

SAMPLE = Path(__file__).parent.parent / "data" / "sample_statement.csv"


def test_clean_upi_description():
    assert clean_description("UPI/SWIGGY/4839201/Payment") == "swiggy"


def test_clean_drops_upi_handle_and_noise():
    assert clean_description("UPI/rahul@okaxis/123/Paid") == ""


def test_exact_merchant():
    assert match_merchant("swiggy")[1] == "Food"


def test_specific_merchant_beats_general():
    assert match_merchant("swiggy instamart")[1] == "Groceries"


def test_fuzzy_typo_is_flagged_for_review():
    merchant, category, conf = match_merchant("swigy")
    assert category == "Food" and 0.85 <= conf < 0.95


def test_unknown_person_is_uncategorized():
    assert match_merchant("rahul sharma")[1] == "Uncategorized"


def test_user_rule_overrides():
    assert match_merchant("rahul sharma", {"rahul sharma": "Rent"})[1] == "Rent"


def test_sample_statement_end_to_end():
    raw = load_statement(SAMPLE)
    expenses = raw[raw["type"] == "debit"]
    assert len(raw) == 27 and len(expenses) == 26
    out = categorize(expenses.reset_index(drop=True))
    assert out["needs_review"].sum() >= 2   # the two people + the typo
    assert out.loc[out["description"].str.contains("DMART"), "category"].iloc[0] == "Groceries"


def test_bank_upi_narration_uses_payee_segment():
    text = "UPI-DOMINOS PIZZA-DOMINOSPIZZAONLINE@PTYBL-YESB0PTMUPI-123456789012-PAYMENT"
    assert clean_description(text) == "dominos pizza"
    assert match_merchant(clean_description(text))[1] == "Food"


def test_local_shop_keywords():
    assert match_merchant("coffee with college")[1] == "Food"
    assert match_merchant("shri kateel bakery")[1] == "Food"


def test_loader_finds_header_below_bank_preamble(tmp_path):
    csv = tmp_path / "stmt.csv"
    csv.write_text(
        "ACCOUNT STATEMENT\nCustomer: someone\n\n"
        "Date,Narration,Chq./Ref.No.,Value Dt,Withdrawal Amt.,Deposit Amt.,Closing Balance\n"
        "********,********,********,********,********,********,********\n"
        "01/09/26,UPI-SWIGGY-SWIGGY@ICICI-ICIC0000-1-X,1,01/09/26,250.50,,999\n"
        "02/09/26,SALARY,2,02/09/26,,5000,5999\n"
        "STATEMENT SUMMARY,,,,,,\n"
    )
    out = load_statement(csv)
    assert len(out) == 2
    assert out["type"].tolist() == ["debit", "credit"]
    assert out["date"].iloc[0].month == 9 and out["date"].iloc[0].day == 1
    assert out["amount"].iloc[0] == 250.50
