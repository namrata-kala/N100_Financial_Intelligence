"""
pages/08_reports.py
Annual Reports Screen — Nifty 100 Analytics Dashboard
Uses real BSE PDF links from the documents table.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import pandas as pd
import requests

from dashboard.utils.db import get_companies

st.set_page_config(page_title="Annual Reports · Nifty 100", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:linear-gradient(135deg,#0F0F1A 0%,#1A1A2E 50%,#16213E 100%);}
[data-testid="stSidebar"]{background:rgba(255,255,255,0.04);backdrop-filter:blur(10px);border-right:1px solid rgba(255,255,255,0.08);}
.section-header{font-size:1.2rem;font-weight:600;color:#E2E8F0;padding:16px 0 8px 0;border-bottom:1px solid rgba(255,255,255,0.08);margin-bottom:16px;}
.report-card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:16px 20px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;}
.badge-red{display:inline-block;background:rgba(239,68,68,0.15);color:#EF4444;border:1px solid rgba(239,68,68,0.3);border-radius:20px;padding:4px 12px;font-size:0.8rem;}
.badge-green{display:inline-block;background:rgba(16,185,129,0.15);color:#10B981;border:1px solid rgba(16,185,129,0.3);border-radius:20px;padding:4px 12px;font-size:0.8rem;}
</style>""", unsafe_allow_html=True)


@st.cache_data(ttl=600)
def _get_documents(ticker: str) -> pd.DataFrame:
    """Load documents for a ticker — uses the documents table if available."""
    try:
        from dashboard.utils.db import get_documents
        return get_documents(ticker)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def check_url_status(url: str) -> bool:
    """Check if a URL returns 200."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.head(url, timeout=5, allow_redirects=True, headers=headers)
        if r.status_code >= 400:
            # Fallback to GET for sites that block HEAD
            r = requests.get(url, timeout=5, stream=True, headers=headers)
            r.close()
        return r.status_code < 400
    except Exception:
        return False


companies = get_companies()
ticker_opts = [f"{r.ticker} — {r.name}" for r in companies.itertuples()]

with st.sidebar:
    st.markdown("### 📄 Annual Reports")
    search = st.selectbox("🔍 Select Company", ticker_opts, key="reports_search")
    check_live = st.checkbox("🔗 Check link availability (slower)", value=False, key="reports_check_live")

ticker = search.split(" — ")[0].strip()
comp_row = companies[companies["ticker"] == ticker]

st.markdown(f"""
<div style="padding:8px 0 24px 0;">
    <h1 style="font-size:2rem;font-weight:700;color:#E2E8F0;margin:0;">📄 Annual Reports</h1>
    <p style="color:rgba(226,232,240,0.5);margin:4px 0 0 0;">BSE annual report PDF links · <strong style="color:#7C3AED">{ticker}</strong></p>
</div>
""", unsafe_allow_html=True)

if comp_row.empty:
    st.error("❌ Ticker not found — please try another")
    st.stop()

comp = comp_row.iloc[0]

# ── Company info ───────────────────────────────────────────────────────────────
about_text = comp.get("about", "") or ""
st.markdown(f"""
<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(124,58,237,0.3);
            border-radius:16px;padding:20px;margin-bottom:24px;">
    <div style="font-size:1.4rem;font-weight:700;color:#E2E8F0;">{comp['name']}</div>
    <div style="color:#7C3AED;font-weight:600;margin:4px 0;">NSE: {comp['ticker']}</div>
    <div style="color:rgba(226,232,240,0.6);font-size:0.85rem;margin-top:8px;">{comp['sector']} · {comp.get('sub_sector', '')}</div>
    {'<div style="color:rgba(226,232,240,0.5);font-size:0.82rem;margin-top:8px;">' + about_text[:200] + '</div>' if about_text else ''}
</div>
""", unsafe_allow_html=True)

# ── Report links from database ─────────────────────────────────────────────────
docs_df = _get_documents(ticker)

if docs_df.empty:
    st.warning("⚠️ No annual report links available for this company in the database.")
    st.stop()

st.markdown(f'<div class="section-header">📋 Available Annual Reports ({len(docs_df)} found)</div>', unsafe_allow_html=True)

if check_live:
    with st.spinner("Checking report availability..."):
        statuses = {}
        for _, row in docs_df.iterrows():
            url = row["annual_report_url"]
            statuses[row["year"]] = check_url_status(url) if url and url.startswith("http") else False
else:
    statuses = {}

for _, row in docs_df.iterrows():
    yr = row["year"]
    url = row["annual_report_url"]

    if not url or not str(url).startswith("http"):
        badge = '<span class="badge-red">✗ No URL</span>'
        link = '<span style="color:rgba(226,232,240,0.3);">—</span>'
    elif check_live:
        available = statuses.get(yr, False)
        if available:
            badge = '<span class="badge-green">✓ Available</span>'
            link = f'<a href="{url}" target="_blank" style="color:#7C3AED;text-decoration:none;font-weight:500;">⬇️ Download PDF</a>'
        else:
            badge = '<span class="badge-red">✗ Report unavailable</span>'
            link = f'<a href="{url}" target="_blank" style="color:rgba(226,232,240,0.4);text-decoration:none;">Try anyway →</a>'
    else:
        badge = '<span style="background:rgba(6,182,212,0.15);color:#06B6D4;border:1px solid rgba(6,182,212,0.3);border-radius:20px;padding:4px 12px;font-size:0.8rem;">📎 Link available</span>'
        link = f'<a href="{url}" target="_blank" style="color:#7C3AED;text-decoration:none;font-weight:500;">⬇️ Open PDF</a>'

    st.markdown(f"""
    <div class="report-card">
        <div>
            <div style="font-weight:600;color:#E2E8F0;">Annual Report FY {yr}</div>
            <div style="font-size:0.72rem;color:rgba(226,232,240,0.35);margin-top:2px;word-break:break-all;max-width:600px;">{url if url else 'No URL'}</div>
        </div>
        <div style="display:flex;align-items:center;gap:12px;">
            {badge}
            {link}
        </div>
    </div>
    """, unsafe_allow_html=True)
