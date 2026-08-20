"""
src/dashboard/utils/db.py
Shared cached data loader for Nifty 100 Analytics Dashboard.
All functions use @st.cache_data(ttl=600) for 10-minute caching.
"""

import os
import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "nifty100.db")


def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH, check_same_thread=False)


# ─────────────────────────────────────────────────────────────────────────────
# Core Loaders
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    """Return all 92 companies with metadata."""
    conn = _get_conn()
    df = pd.read_sql_query("""
        SELECT c.company_id, c.ticker, c.name, c.sector, c.sub_sector,
               c.peer_group, c.about, c.pros, c.cons, c.capital_pattern,
               pg.group_name
        FROM companies c
        LEFT JOIN peer_groups pg ON pg.group_id = c.peer_group
        ORDER BY c.company_id
    """, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_ratios(ticker: str, year: int = None) -> pd.DataFrame:
    """Return financial ratios for a given ticker, optionally filtered by year."""
    conn = _get_conn()
    if year:
        df = pd.read_sql_query("""
            SELECT r.* FROM ratios r
            JOIN companies c ON c.company_id = r.company_id
            WHERE c.ticker = ? AND r.year = ?
        """, conn, params=(ticker, year))
    else:
        df = pd.read_sql_query("""
            SELECT r.* FROM ratios r
            JOIN companies c ON c.company_id = r.company_id
            WHERE c.ticker = ?
            ORDER BY r.year
        """, conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pl(ticker: str) -> pd.DataFrame:
    """Return P&L history for a given ticker."""
    conn = _get_conn()
    df = pd.read_sql_query("""
        SELECT p.* FROM pl p
        JOIN companies c ON c.company_id = p.company_id
        WHERE c.ticker = ?
        ORDER BY p.year
    """, conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_bs(ticker: str) -> pd.DataFrame:
    """Return balance sheet history for a given ticker."""
    conn = _get_conn()
    df = pd.read_sql_query("""
        SELECT b.* FROM balance_sheet b
        JOIN companies c ON c.company_id = b.company_id
        WHERE c.ticker = ?
        ORDER BY b.year
    """, conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_cf(ticker: str) -> pd.DataFrame:
    """Return cash flow history for a given ticker."""
    conn = _get_conn()
    df = pd.read_sql_query("""
        SELECT cf.* FROM cash_flow cf
        JOIN companies c ON c.company_id = cf.company_id
        WHERE c.ticker = ?
        ORDER BY cf.year
    """, conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    """Return sector-level aggregates for the latest year."""
    conn = _get_conn()
    df = pd.read_sql_query("""
        SELECT c.sector,
               COUNT(DISTINCT c.company_id)              AS company_count,
               ROUND(AVG(r.roe), 2)                      AS avg_roe,
               ROUND(AVG(r.pe), 2)                       AS avg_pe,
               ROUND(AVG(r.opm), 2)                      AS avg_opm,
               ROUND(AVG(r.revenue_cagr_5yr), 2)         AS avg_rev_cagr,
               ROUND(AVG(r.composite_score), 2)          AS avg_composite,
               ROUND(SUM(v.market_cap), 2)               AS total_market_cap
        FROM companies c
        JOIN ratios r ON r.company_id = c.company_id AND r.year = 2024
        JOIN valuation v ON v.company_id = c.company_id AND v.year = 2024
        GROUP BY c.sector
        ORDER BY total_market_cap DESC
    """, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peers(group_name: str) -> pd.DataFrame:
    """Return all companies and their latest ratios for a given peer group."""
    conn = _get_conn()
    df = pd.read_sql_query("""
        SELECT c.ticker, c.name, c.sector, c.sub_sector,
               r.roe, r.roce, r.pe, r.pb, r.ev_ebitda, r.de,
               r.opm, r.npm, r.revenue_cagr_5yr, r.composite_score,
               r.dividend_yield,
               v.market_cap
        FROM companies c
        JOIN peer_groups pg ON pg.group_id = c.peer_group
        JOIN ratios r ON r.company_id = c.company_id AND r.year = 2024
        JOIN valuation v ON v.company_id = c.company_id AND v.year = 2024
        WHERE pg.group_name = ?
        ORDER BY r.composite_score DESC
    """, conn, params=(group_name,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_valuation(ticker: str) -> pd.DataFrame:
    """Return valuation data for a given ticker (all years)."""
    conn = _get_conn()
    df = pd.read_sql_query("""
        SELECT v.* FROM valuation v
        JOIN companies c ON c.company_id = v.company_id
        WHERE c.ticker = ?
        ORDER BY v.year
    """, conn, params=(ticker,))
    conn.close()
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Convenience helpers
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=600)
def get_home_kpis(year: int = 2024) -> dict:
    """Return aggregate KPIs for the Home screen."""
    conn = _get_conn()
    df = pd.read_sql_query(f"""
        SELECT r.roe, r.pe, r.de, r.revenue_cagr_5yr, r.composite_score, r.dividend_yield
        FROM ratios r
        WHERE r.year = {year}
    """, conn)
    bs = pd.read_sql_query(f"""
        SELECT b.total_debt FROM balance_sheet b WHERE b.year = {year}
    """, conn)
    conn.close()

    debt_free = int((bs["total_debt"] < 1).sum())
    return {
        "avg_roe":          round(float(df["roe"].mean()), 1),
        "median_pe":        round(float(df["pe"].median()), 1),
        "median_de":        round(float(df["de"].median()), 2),
        "total_companies":  int(len(df)),
        "median_rev_cagr":  round(float(df["revenue_cagr_5yr"].median()), 1),
        "debt_free_count":  debt_free,
    }


@st.cache_data(ttl=600)
def get_top_companies(year: int = 2024, n: int = 5) -> pd.DataFrame:
    """Return top-N companies by composite quality score."""
    conn = _get_conn()
    df = pd.read_sql_query(f"""
        SELECT c.ticker, c.name, c.sector,
               r.composite_score, r.roe, r.roce, r.pe, r.opm, r.revenue_cagr_5yr
        FROM ratios r
        JOIN companies c ON c.company_id = r.company_id
        WHERE r.year = {year}
        ORDER BY r.composite_score DESC
        LIMIT {n}
    """, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_all_ratios_year(year: int = 2024) -> pd.DataFrame:
    """Return ratios for all companies in a given year (for screener)."""
    conn = _get_conn()
    df = pd.read_sql_query(f"""
        SELECT c.company_id, c.ticker, c.name, c.sector, c.sub_sector,
               r.roe, r.roce, r.pe, r.pb, r.de, r.opm, r.npm,
               r.revenue_cagr_5yr, r.pat_cagr_5yr, r.dividend_yield, r.icr,
               r.composite_score, cf.fcf,
               v.market_cap
        FROM ratios r
        JOIN companies c ON c.company_id = r.company_id
        JOIN cash_flow cf ON cf.company_id = r.company_id AND cf.year = r.year
        JOIN valuation v ON v.company_id = r.company_id AND v.year = r.year
        WHERE r.year = {year}
    """, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_sector_bubble(year: int = 2024) -> pd.DataFrame:
    """Return sector bubble chart data."""
    conn = _get_conn()
    df = pd.read_sql_query(f"""
        SELECT c.ticker, c.name, c.sector, c.sub_sector,
               p.revenue, r.roe, v.market_cap
        FROM pl p
        JOIN companies c ON c.company_id = p.company_id
        JOIN ratios r ON r.company_id = p.company_id AND r.year = p.year
        JOIN valuation v ON v.company_id = p.company_id AND v.year = p.year
        WHERE p.year = {year}
    """, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_all_peer_groups() -> list:
    conn = _get_conn()
    c = conn.cursor()
    rows = c.execute("SELECT group_name FROM peer_groups ORDER BY group_id").fetchall()
    conn.close()
    return [r[0] for r in rows]


@st.cache_data(ttl=600)
def get_documents(ticker: str) -> pd.DataFrame:
    conn = _get_conn()
    df = pd.read_sql_query('''
        SELECT d.year, d.annual_report_url FROM documents d
        JOIN companies c ON c.company_id = d.company_id
        WHERE c.ticker = ?
        ORDER BY d.year DESC
    ''', conn, params=(ticker,))
    conn.close()
    return df
