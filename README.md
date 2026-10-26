# AI-Powered Personal Finance Manager (v1)

Upload a bank statement → transactions are cleaned, merchants identified, categories assigned →
unclear ones are put to you → dashboard with charts and insights.

## Run
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
Tick **Use sample statement** in the sidebar to try it instantly. Run tests with `pytest`.

## Statement format
CSV or Excel with a date column, a description/narration column, and either
Debit + Credit columns or a single Amount column (negative = money out).

## How it works
`ingestion.py` normalizes → `cleaning.py` strips IDs/noise → `categorizer.py` matches merchants
(your saved corrections → exact keywords → fuzzy match) → anything unsure goes to you →
`analytics.py` builds the summary and insights → `app.py` shows it.

To teach it new merchants, add them to `MERCHANT_MAP` in `src/config.py`.
Your corrections are remembered in `data/user_rules.json`.

## Privacy
Everything runs locally. Don't commit real statements to GitHub.

## Next features
ML classifier for unknown merchants, PDF statements, monthly trends, report export.
