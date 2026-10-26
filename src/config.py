"""Central settings: categories, merchant dictionary, thresholds."""

UNCATEGORIZED = "Uncategorized"

CATEGORIES = [
    "Food",
    "Groceries",
    "Transportation",
    "Shopping",
    "Rent",
    "Medical",
    "Bills & Utilities",
    "Entertainment",
    "Miscellaneous",
]

# keyword (lowercase, as it appears after cleaning) -> category
# Add new merchants here, no other code changes needed.
MERCHANT_MAP = {
    # Food
    "swiggy": "Food",
    "zomato": "Food",
    "dominos": "Food",
    "mcdonalds": "Food",
    "starbucks": "Food",
    "kfc": "Food",
    "subway": "Food",
    "bakery": "Food",
    "coffee": "Food",
    "tea": "Food",
    "juice": "Food",
    "cafe": "Food",
    "canteen": "Food",
    "maggie": "Food",
    "scoops": "Food",
    "restaurant": "Food",
    # Groceries
    "swiggy instamart": "Groceries",
    "instamart": "Groceries",
    "blinkit": "Groceries",
    "zepto": "Groceries",
    "bigbasket": "Groceries",
    "dmart": "Groceries",
    # Transportation
    "uber": "Transportation",
    "ola": "Transportation",
    "rapido": "Transportation",
    "irctc": "Transportation",
    "redbus": "Transportation",
    "indian oil": "Transportation",
    "fuel": "Transportation",
    "petrol": "Transportation",
    # Shopping
    "amazon": "Shopping",
    "amzn": "Shopping",
    "flipkart": "Shopping",
    "myntra": "Shopping",
    "ajio": "Shopping",
    "meesho": "Shopping",
    # Rent
    "rent": "Rent",
    # Medical
    "apollo": "Medical",
    "pharmeasy": "Medical",
    "netmeds": "Medical",
    "medplus": "Medical",
    "pharmacy": "Medical",
    "hospital": "Medical",
    # Bills & Utilities
    "airtel": "Bills & Utilities",
    "jio": "Bills & Utilities",
    "bescom": "Bills & Utilities",
    "electricity": "Bills & Utilities",
    "broadband": "Bills & Utilities",
    "instaalertchg": "Bills & Utilities",   # bank SMS-alert charges
    # Entertainment
    "netflix": "Entertainment",
    "spotify": "Entertainment",
    "hotstar": "Entertainment",
    "bookmyshow": "Entertainment",
    "theatre": "Entertainment",
    "cinema": "Entertainment",
    # Miscellaneous
    "atm": "Miscellaneous",
    "euronet": "Miscellaneous",             # ATM operator
}

FUZZY_CUTOFF = 85       # min RapidFuzz score (0-100) to accept a fuzzy merchant match
REVIEW_THRESHOLD = 0.9  # confidence below this -> ask the user
