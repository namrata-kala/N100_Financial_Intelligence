"""
pages/02_profile.py
Company Profile Screen — Nifty 100 Analytics Dashboard
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from dashboard.utils.db import get_companies, get_ratios, get_pl, get_cf, get_bs

st.set_page_config(page_title="Company Profile · Nifty 100", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:linear-gradient(135deg,#0F0F1A 0%,#1A1A2E 50%,#16213E 100%);}
[data-testid="stSidebar"]{background:rgba(255,255,255,0.04);backdrop-filter:blur(10px);border-right:1px solid rgba(255,255,255,0.08);}
.kpi-card{background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.10);border-radius:16px;padding:20px 24px;text-align:center;}
.kpi-label{font-size:0.75rem;font-weight:500;color:rgba(226,232,240,0.6);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;}
.kpi-value{font-size:1.8rem;font-weight:700;background:linear-gradient(135deg,#7C3AED,#06B6D4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.kpi-sub{font-size:0.72rem;color:rgba(226,232,240,0.45);margin-top:4px;}
.company-card{background:rgba(255,255,255,0.04);border:1px solid rgba(124,58,237,0.3);border-radius:16px;padding:24px;margin-bottom:20px;}
.badge-green{display:inline-block;background:rgba(16,185,129,0.15);color:#10B981;border:1px solid rgba(16,185,129,0.3);border-radius:20px;padding:4px 12px;font-size:0.8rem;margin:3px 2px;}
.badge-red{display:inline-block;background:rgba(239,68,68,0.15);color:#EF4444;border:1px solid rgba(239,68,68,0.3);border-radius:20px;padding:4px 12px;font-size:0.8rem;margin:3px 2px;}
.section-header{font-size:1.2rem;font-weight:600;color:#E2E8F0;padding:16px 0 8px 0;border-bottom:1px solid rgba(255,255,255,0.08);margin-bottom:16px;}
.stButton>button{background:linear-gradient(135deg,#7C3AED,#4F46E5);color:white;border:none;border-radius:8px;font-weight:500;}
</style>""", unsafe_allow_html=True)

# ── Load all companies for search ──────────────────────────────────────────────
@st.cache_data(ttl=600)
def get_company_list():
    df = get_companies()
    return df[["ticker", "name", "sector", "sub_sector", "about", "pros", "cons", "peer_group"]]

companies = get_company_list()
ticker_options = [f"{row.ticker} — {row.name}" for row in companies.itertuples()]

# ── Sidebar search ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏢 Company Profile")
    search_input = st.selectbox(
        "🔍 Search company or ticker",
        options=ticker_options,
        index=0,
        help="Type to search by ticker or company name",
    )

# ── Resolve selected company ───────────────────────────────────────────────────
selected_ticker = search_input.split(" — ")[0].strip()
comp_row = companies[companies["ticker"] == selected_ticker]

if comp_row.empty:
    st.error("❌ Ticker not found — please try another")
    st.stop()

comp = comp_row.iloc[0]

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="padding:8px 0 16px 0;">
    <h1 style="font-size:2rem;font-weight:700;color:#E2E8F0;margin:0;">🏢 Company Profile</h1>
</div>
""", unsafe_allow_html=True)

# ── Company card ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="company-card">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;">
        <div>
            <div style="font-size:1.8rem;font-weight:700;color:#E2E8F0;">{comp['name']}</div>
            <div style="font-size:1rem;color:#7C3AED;font-weight:600;margin:4px 0;">{comp['ticker']}</div>
            <div style="margin-top:8px;">
                <span class="badge-green">{comp['sector']}</span>
                <span class="badge-blue" style="background:rgba(6,182,212,0.15);color:#06B6D4;border:1px solid rgba(6,182,212,0.3);">{comp['sub_sector']}</span>
                <span class="badge-yellow" style="background:rgba(245,158,11,0.15);color:#F59E0B;border:1px solid rgba(245,158,11,0.3);">NSE: {comp['ticker']}</span>
            </div>
        </div>
        <div style="max-width:500px;color:rgba(226,232,240,0.7);font-size:0.88rem;line-height:1.6;">
            {comp['about']}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Fetch data ─────────────────────────────────────────────────────────────────
ratios = get_ratios(selected_ticker)
pl_df  = get_pl(selected_ticker)
cf_df  = get_cf(selected_ticker)
bs_df  = get_bs(selected_ticker)

if ratios.empty or pl_df.empty:
    st.warning(f"⚠️ Ticker **{selected_ticker}** — data available for limited years only.")
    st.stop()

latest_ratio = ratios.iloc[-1]
latest_cf    = cf_df.iloc[-1] if not cf_df.empty else None

# ── 6 KPI tiles ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📌 Key Metrics (Latest Year)</div>', unsafe_allow_html=True)
kpi_cols = st.columns(6)
kpis_data = [
    ("ROE",         f"{latest_ratio['roe']:.1f}%" if pd.notnull(latest_ratio['roe']) else "N/A",      "Return on Equity"),
    ("ROCE",        f"{latest_ratio['roce']:.1f}%" if pd.notnull(latest_ratio['roce']) else "N/A",     "Return on Cap Employed"),
    ("NPM",         f"{latest_ratio['npm']:.1f}%" if pd.notnull(latest_ratio['npm']) else "N/A",      "Net Profit Margin"),
    ("D/E",         f"{latest_ratio['de']:.2f}x" if pd.notnull(latest_ratio['de']) else "N/A",       "Debt-to-Equity"),
    ("Rev CAGR 5Y", f"{latest_ratio['revenue_cagr_5yr']:.1f}%" if pd.notnull(latest_ratio['revenue_cagr_5yr']) else "N/A", "Revenue CAGR 5 Year"),
    ("FCF",         f"₹{latest_cf['fcf']:.0f} Cr" if latest_cf is not None and pd.notnull(latest_cf['fcf']) else "N/A", "Free Cash Flow"),
]
for col, (label, val, sub) in zip(kpi_cols, kpis_data):
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{val}</div>
            <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Revenue & PAT bar chart ────────────────────────────────────────────────────
st.markdown('<div class="section-header">📈 Revenue & Net Profit (10 Year)</div>', unsafe_allow_html=True)

fig1 = go.Figure()
fig1.add_trace(go.Bar(
    name="Revenue (₹ Cr)", x=pl_df["year"], y=pl_df["revenue"],
    marker_color="#7C3AED", opacity=0.85, yaxis="y1",
))
fig1.add_trace(go.Bar(
    name="Net Profit (₹ Cr)", x=pl_df["year"], y=pl_df["pat"],
    marker_color="#06B6D4", opacity=0.85, yaxis="y1",
))
fig1.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font_color="#E2E8F0", barmode="group",
    xaxis=dict(tickmode="linear", dtick=1, gridcolor="rgba(255,255,255,0.05)"),
    yaxis=dict(title="₹ Crore", gridcolor="rgba(255,255,255,0.05)"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    margin=dict(t=40, b=40), height=340, hovermode="x unified",
)
st.plotly_chart(fig1, use_container_width=True, key="profile_rev_pat")

# ── ROE & ROCE dual-axis line chart ────────────────────────────────────────────
st.markdown('<div class="section-header">📉 ROE & ROCE Trend (10 Year)</div>', unsafe_allow_html=True)

fig2 = make_subplots(specs=[[{"secondary_y": True}]])
fig2.add_trace(go.Scatter(
    name="ROE %", x=ratios["year"], y=ratios["roe"],
    mode="lines+markers",
    line=dict(color="#7C3AED", width=2.5),
    marker=dict(size=7),
    fill="tozeroy", fillcolor="rgba(124,58,237,0.08)",
), secondary_y=False)
fig2.add_trace(go.Scatter(
    name="ROCE %", x=ratios["year"], y=ratios["roce"],
    mode="lines+markers",
    line=dict(color="#10B981", width=2.5, dash="dot"),
    marker=dict(size=7),
), secondary_y=True)
fig2.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font_color="#E2E8F0",
    xaxis=dict(tickmode="linear", dtick=1, gridcolor="rgba(255,255,255,0.05)"),
    yaxis=dict(title="ROE %", gridcolor="rgba(255,255,255,0.05)"),
    yaxis2=dict(title="ROCE %", showgrid=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    margin=dict(t=40, b=40), height=320, hovermode="x unified",
)
st.plotly_chart(fig2, use_container_width=True, key="profile_roe_roce")

# ── Pros & Cons ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">✅ Strengths & ⚠️ Risks</div>', unsafe_allow_html=True)
pros_list = str(comp["pros"]).split("|") if comp["pros"] else []
cons_list = str(comp["cons"]).split("|") if comp["cons"] else []

col_pros, col_cons = st.columns(2)
with col_pros:
    st.markdown("**✅ Strengths**")
    for p in pros_list:
        if p.strip():
            st.markdown(f'<span class="badge-green">✓ {p.strip()}</span>', unsafe_allow_html=True)

with col_cons:
    st.markdown("**⚠️ Risks**")
    for c in cons_list:
        if c.strip():
            st.markdown(f'<span class="badge-red">✗ {c.strip()}</span>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Historical ratio table ─────────────────────────────────────────────────────
with st.expander("📋 Full Historical Ratios Table"):
    display_ratios = ratios[["year","roe","roce","pe","pb","de","opm","npm",
                              "revenue_cagr_5yr","dividend_yield","composite_score"]].copy()
    display_ratios.columns = ["Year","ROE %","ROCE %","P/E","P/B","D/E","OPM %","NPM %",
                               "Rev CAGR 5Y %","Div Yield %","Quality Score"]
    st.dataframe(display_ratios, use_container_width=True, hide_index=True)
