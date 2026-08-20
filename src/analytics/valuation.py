"""
src/analytics/valuation.py
Valuation module for Nifty 100 Analytics Dashboard.
Computes FCF yield, sector P/E flags, and generates output files.

Usage:
    python src/analytics/valuation.py
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np

BASE_DIR      = os.path.join(os.path.dirname(__file__), "..", "..")
DB_PATH       = os.path.join(BASE_DIR, "data", "nifty100.db")
MCap_PATH     = os.path.join(BASE_DIR, "data", "market_cap.xlsx")
OUTPUT_DIR    = os.path.join(BASE_DIR, "output")
SUMMARY_PATH  = os.path.join(OUTPUT_DIR, "valuation_summary.xlsx")
FLAGS_PATH    = os.path.join(OUTPUT_DIR, "valuation_flags.csv")

LATEST_YEAR   = 2024
FLAG_YEAR     = LATEST_YEAR


def load_data() -> pd.DataFrame:
    """Load companies, ratios, cash flows and market cap into a single DataFrame."""
    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql_query(
        "SELECT company_id, ticker, name, sector FROM companies", conn
    )
    ratios = pd.read_sql_query(f"""
        SELECT company_id, year, pe, pb, ev_ebitda, revenue_cagr_5yr
        FROM ratios WHERE year = {LATEST_YEAR}
    """, conn)
    ratios_5yr = pd.read_sql_query(f"""
        SELECT company_id, year, pe
        FROM ratios WHERE year BETWEEN {LATEST_YEAR-4} AND {LATEST_YEAR}
    """, conn)
    cf = pd.read_sql_query(f"""
        SELECT company_id, fcf FROM cash_flow WHERE year = {LATEST_YEAR}
    """, conn)
    conn.close()

    # 5-year median P/E per company
    five_yr_median = (
        ratios_5yr.groupby("company_id")["pe"]
        .median()
        .reset_index()
        .rename(columns={"pe": "5yr_median_pe"})
    )

    # Load market cap from Excel
    mcap_df = pd.read_excel(MCap_PATH)
    # The pivot has company_id, ticker, name, sector, then year columns
    year_col = str(LATEST_YEAR)
    if year_col not in mcap_df.columns:
        # Fallback: use the last numeric column
        year_cols = [c for c in mcap_df.columns if c.isdigit()]
        year_col = year_cols[-1] if year_cols else None

    if year_col:
        mcap = mcap_df[["company_id", year_col]].rename(columns={year_col: "market_cap_crore"})
    else:
        # Estimate from P/E × PAT if no market cap
        mcap = pd.DataFrame({"company_id": companies["company_id"], "market_cap_crore": [10000.0] * len(companies)})

    # Merge all
    df = (
        companies
        .merge(ratios,      on="company_id", how="left")
        .merge(five_yr_median, on="company_id", how="left")
        .merge(cf,          on="company_id", how="left")
        .merge(mcap,        on="company_id", how="left")
    )

    return df


def compute_fcf_yield(df: pd.DataFrame) -> pd.DataFrame:
    """FCF yield = FCF / Market Cap × 100"""
    df = df.copy()
    df["fcf_yield_pct"] = (
        df["fcf"] / df["market_cap_crore"].replace(0, np.nan) * 100
    ).round(2)
    return df


def compute_sector_median_pe(df: pd.DataFrame) -> pd.DataFrame:
    """Compute sector median P/E and % difference from sector median."""
    sector_med = (
        df.groupby("sector")["pe"]
        .median()
        .reset_index()
        .rename(columns={"pe": "sector_median_pe"})
    )
    df = df.merge(sector_med, on="sector", how="left")
    df["pe_vs_sector_median_pct"] = (
        (df["pe"] - df["sector_median_pe"]) / df["sector_median_pe"] * 100
    ).round(2)
    return df


def apply_valuation_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply overvaluation flags:
    - Caution  : P/E > sector_median_pe × 1.5
    - Discount : P/E < sector_median_pe × 0.7
    - Fair     : otherwise
    """
    df = df.copy()

    def flag_row(row):
        pe   = row["pe"]
        smed = row["sector_median_pe"]
        if pd.isna(pe) or pd.isna(smed) or smed == 0:
            return "Fair"
        if pe > smed * 1.5:
            return "Caution"
        elif pe < smed * 0.7:
            return "Discount"
        return "Fair"

    df["flag"] = df.apply(flag_row, axis=1)
    return df


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build the final valuation_summary DataFrame."""
    summary = df[[
        "company_id", "name", "sector",
        "pe", "pb", "ev_ebitda",
        "fcf_yield_pct",
        "5yr_median_pe",
        "pe_vs_sector_median_pct",
        "flag",
    ]].copy()

    summary = summary.rename(columns={
        "name":               "company_name",
        "pe":                 "P/E",
        "pb":                 "P/B",
        "ev_ebitda":          "EV/EBITDA",
        "fcf_yield_pct":      "FCF_yield_pct",
        "5yr_median_pe":      "5yr_median_PE",
        "pe_vs_sector_median_pct": "PE_vs_sector_median_pct",
    })

    # Format
    for col in ["P/E", "P/B", "EV/EBITDA", "FCF_yield_pct", "5yr_median_PE", "PE_vs_sector_median_pct"]:
        summary[col] = summary[col].apply(lambda x: round(float(x), 2) if pd.notna(x) else None)

    return summary.reset_index(drop=True)


def save_outputs(summary: pd.DataFrame) -> None:
    """Save valuation_summary.xlsx and valuation_flags.csv."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Full summary — 92 rows
    summary.to_excel(SUMMARY_PATH, index=False)
    print(f"✅ valuation_summary.xlsx saved ({len(summary)} rows) → {SUMMARY_PATH}")

    # Flags only — Caution or Discount
    flags_df = summary[summary["flag"].isin(["Caution", "Discount"])].copy()
    flags_df.to_csv(FLAGS_PATH, index=False)
    print(f"✅ valuation_flags.csv saved ({len(flags_df)} flagged companies) → {FLAGS_PATH}")


def run_valuation() -> pd.DataFrame:
    """Full valuation pipeline."""
    print("🔄 Loading financial data...")
    df = load_data()

    print("📊 Computing FCF yield...")
    df = compute_fcf_yield(df)

    print("📐 Computing sector median P/E...")
    df = compute_sector_median_pe(df)

    print("🚩 Applying valuation flags...")
    df = apply_valuation_flags(df)

    print("📝 Building summary...")
    summary = build_summary(df)

    # Print quick stats
    flag_counts = summary["flag"].value_counts()
    print(f"\n📋 Flag summary:")
    for flag, count in flag_counts.items():
        emoji = {"Caution": "⚠️", "Discount": "💚", "Fair": "✅"}.get(flag, "")
        print(f"   {emoji} {flag}: {count} companies")

    save_outputs(summary)
    print("\n🎉 Valuation module complete!")
    return summary


if __name__ == "__main__":
    run_valuation()
