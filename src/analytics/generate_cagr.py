from pathlib import Path
import sqlite3
import pandas as pd

from src.analytics.cagr import calculate_cagr

DB_PATH = Path("db/nifty100.db")

conn = sqlite3.connect(DB_PATH)

profit = pd.read_sql(
    """
    SELECT company_id,
           year,
           sales,
           net_profit,
           eps
    FROM profitandloss
    ORDER BY company_id, year
    """,
    conn,
)


def generate_cagr(df, column, years, metric_name):
    """
    Generate CAGR for a given column and time window.
    """

    results = []

    for company, group in df.groupby("company_id"):

        group = group.sort_values("year").reset_index(drop=True)

        if len(group) < years + 1:
            results.append({
                "company_id": company,
                f"{metric_name}_cagr_{years}yr": None,
                f"{metric_name}_cagr_{years}yr_flag": "INSUFFICIENT"
            })
            continue

        start = group.iloc[-(years + 1)][column]
        end = group.iloc[-1][column]

        value, flag = calculate_cagr(start, end, years)

        results.append({
            "company_id": company,
            f"{metric_name}_cagr_{years}yr": value,
            f"{metric_name}_cagr_{years}yr_flag": flag
        })

    return pd.DataFrame(results)


revenue_3 = generate_cagr(profit, "sales", 3, "revenue")
revenue_5 = generate_cagr(profit, "sales", 5, "revenue")
revenue_10 = generate_cagr(profit, "sales", 10, "revenue")

pat_3 = generate_cagr(profit, "net_profit", 3, "pat")
pat_5 = generate_cagr(profit, "net_profit", 5, "pat")
pat_10 = generate_cagr(profit, "net_profit", 10, "pat")

eps_3 = generate_cagr(profit, "eps", 3, "eps")
eps_5 = generate_cagr(profit, "eps", 5, "eps")
eps_10 = generate_cagr(profit, "eps", 10, "eps")

cagr_df = revenue_3

for df in [
    revenue_5,
    revenue_10,
    pat_3,
    pat_5,
    pat_10,
    eps_3,
    eps_5,
    eps_10,
]:
    cagr_df = cagr_df.merge(df, on="company_id", how="left")

print(cagr_df.head())

print("\nColumns:\n")
print(cagr_df.columns.tolist())

from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

cagr_df.to_csv(
    OUTPUT_DIR / "cagr_metrics.csv",
    index=False
)

print("\n✓ Saved output/cagr_metrics.csv")