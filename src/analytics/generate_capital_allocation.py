from pathlib import Path
import sqlite3
import pandas as pd

from src.analytics.cashflow_kpis import (
    cfo_quality_score,
    capital_allocation_pattern,
)

DB_PATH = Path("db/nifty100.db")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

conn = sqlite3.connect(DB_PATH)

cashflow = pd.read_sql("""
SELECT
    company_id,
    year,
    operating_activity,
    investing_activity,
    financing_activity
FROM cashflow
ORDER BY company_id, year
""", conn)

profit = pd.read_sql("""
SELECT
    company_id,
    year,
    net_profit
FROM profitandloss
""", conn)

df = cashflow.merge(
    profit,
    on=["company_id", "year"],
    how="left"
)

results = []

for _, row in df.iterrows():

    _, quality = cfo_quality_score(
        row["operating_activity"],
        row["net_profit"]
    )

    pattern = capital_allocation_pattern(
        row["operating_activity"],
        row["investing_activity"],
        row["financing_activity"],
        quality,
    )

    results.append({
        "company_id": row["company_id"],
        "year": row["year"],
        "cfo_sign": "+" if row["operating_activity"] >= 0 else "-",
        "cfi_sign": "+" if row["investing_activity"] >= 0 else "-",
        "cff_sign": "+" if row["financing_activity"] >= 0 else "-",
        "pattern_label": pattern,
    })

capital_df = pd.DataFrame(results)

capital_df.to_csv(
    OUTPUT_DIR / "capital_allocation.csv",
    index=False,
)

print(capital_df.head())
print("\n✓ Saved output/capital_allocation.csv")

conn.close()