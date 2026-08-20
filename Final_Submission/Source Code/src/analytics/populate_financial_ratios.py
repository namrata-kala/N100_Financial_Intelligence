from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    debt_to_equity,
    interest_coverage,
    asset_turnover,
)

from src.analytics.cashflow_kpis import (
    free_cash_flow,
    capex_intensity,
)
from pathlib import Path
import sqlite3
import pandas as pd

DB_PATH = Path("data/nifty100.db")
OUTPUT = Path("output")

conn = sqlite3.connect(DB_PATH)

profit = pd.read_sql("SELECT * FROM profitandloss", conn)
balance = pd.read_sql("SELECT * FROM balancesheet", conn)
cashflow = pd.read_sql("SELECT * FROM cashflow", conn)

cagr = pd.read_csv(
    OUTPUT / "cagr_metrics.csv"
)

capital = pd.read_csv(
    OUTPUT / "capital_allocation.csv"
)

print("Profit:", profit.shape)
print("Balance:", balance.shape)
print("Cashflow:", cashflow.shape)
print("CAGR:", cagr.shape)
print("Capital:", capital.shape)

master = (
    profit
    .merge(balance, on=["company_id", "year"], how="left")
    .merge(cashflow, on=["company_id", "year"], how="left")
    .merge(cagr, on="company_id", how="left")
)

print("\nMaster DataFrame Shape:", master.shape)
print(master.head())

master["net_profit_margin_pct"] = master.apply(
    lambda r: net_profit_margin(r["net_profit"], r["sales"]),
    axis=1,
)

master["operating_profit_margin_pct"] = master.apply(
    lambda r: operating_profit_margin(r["operating_profit"], r["sales"]),
    axis=1,
)

master["return_on_equity_pct"] = master.apply(
    lambda r: return_on_equity(
        r["net_profit"],
        r["equity_capital"],
        r["reserves"],
    ),
    axis=1,
)

master["debt_to_equity"] = master.apply(
    lambda r: debt_to_equity(
        r["borrowings"],
        r["equity_capital"],
        r["reserves"],
    ),
    axis=1,
)

master["interest_coverage"] = master.apply(
    lambda r: interest_coverage(
        r["operating_profit"],
        r["other_income"],
        r["interest"],
    ),
    axis=1,
)

master["asset_turnover"] = master.apply(
    lambda r: asset_turnover(
        r["sales"],
        r["total_assets"],
    ),
    axis=1,
)

master["free_cash_flow_cr"] = master.apply(
    lambda r: free_cash_flow(
        r["operating_activity"],
        r["investing_activity"],
    ),
    axis=1,
)

master["capex_cr"] = master.apply(
    lambda r: capex_intensity(
        r["investing_activity"],
        r["sales"],
    )[0],
    axis=1,
)

master["book_value_per_share"] = (
    master["equity_capital"] + master["reserves"]
)

master["earnings_per_share"] = master["eps"]

master["dividend_payout_ratio_pct"] = master["dividend_payout"]

master["total_debt_cr"] = master["borrowings"]

master["cash_from_operations_cr"] = master["operating_activity"]

print("\nMaster columns:\n")
for col in master.columns:
    print(col)

financial_ratios_df = master[
    [
        "company_id",
        "year",
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "free_cash_flow_cr",
        "capex_cr",
        "earnings_per_share",
        "book_value_per_share",
        "dividend_payout_ratio_pct",
        "total_debt_cr",
        "cash_from_operations_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "eps_cagr_5yr",
    ]
].copy()

print("\nFinancial Ratios DataFrame")
print(financial_ratios_df.head())
print("\nShape:", financial_ratios_df.shape)

# Replace financial_ratios table contents

cursor = conn.cursor()

cursor.execute("DELETE FROM financial_ratios")
conn.commit()

financial_ratios_df.to_sql(
    "financial_ratios",
    conn,
    if_exists="append",
    index=False,
)

print("\n✓ financial_ratios table populated")

count = pd.read_sql(
    "SELECT COUNT(*) AS rows FROM financial_ratios",
    conn,
)

print(count)

conn.close()