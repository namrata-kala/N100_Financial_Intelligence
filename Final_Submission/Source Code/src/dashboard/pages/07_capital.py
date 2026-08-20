"""
pages/07_capital.py
Capital Allocation Map Screen — Nifty 100 Analytics Dashboard
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from dashboard.utils.db import get_companies, get_all_ratios_year

st.set_page_config(page_title="Capital Allocation · Nifty 100", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:linear-gradient(135deg,#0F0F1A 0%,#1A1A2E 50%,#16213E 100%);}
[data-testid="stSidebar"]{background:rgba(255,255,255,0.04);backdrop-filter:blur(10px);border-right:1px solid rgba(255,255,255,0.08);}
.section-header{font-size:1.2rem;font-weight:600;color:#E2E8F0;padding:16px 0 8px 0;border-bottom:1px solid rgba(255,255,255,0.08);margin-bottom:16px;}
.badge-blue{display:inline-block;background:rgba(6,182,212,0.15);color:#06B6D4;border:1px solid rgba(6,182,212,0.3);border-radius:20px;padding:4px 12px;font-size:0.8rem;margin:3px 2px;}
</style>""", unsafe_allow_html=True)

# ── Load data ──────────────────────────────────────────────────────────────────
companies_df = get_companies()[["company_id","ticker","name","sector","capital_pattern"]]
ratios_df    = get_all_ratios_year(year=2024)[["company_id","market_cap","fcf","dividend_yield","de","roe"]]
merged       = companies_df.merge(ratios_df, on="company_id", how="left")
merged["market_cap"] = merged["market_cap"].fillna(1000)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🗺️ Capital Allocation Map")
    st.info("Click a pattern in the treemap to see the company list below.")

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:8px 0 24px 0;">
    <h1 style="font-size:2rem;font-weight:700;color:#E2E8F0;margin:0;">🗺️ Capital Allocation Map</h1>
    <p style="color:rgba(226,232,240,0.5);margin:4px 0 0 0;">92 companies grouped by capital allocation behaviour</p>
</div>
""", unsafe_allow_html=True)

# ── Treemap ────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🌳 Treemap — Companies by Capital Allocation Pattern</div>', unsafe_allow_html=True)

fig_tree = px.treemap(
    merged,
    path=["capital_pattern", "sector", "name"],
    values="market_cap",
    color="roe",
    color_continuous_scale=["#1A1A2E","#4F46E5","#7C3AED","#06B6D4","#10B981"],
    color_continuous_midpoint=merged["roe"].median(),
    custom_data=["ticker","sector","roe","de"],
    hover_data={"market_cap": ":.0f"},
    labels={"market_cap": "Market Cap (₹ Cr)", "roe": "ROE %", "capital_pattern": "Pattern"},
)
fig_tree.update_traces(
    hovertemplate="<b>%{label}</b><br>Market Cap: ₹%{value:,.0f} Cr<br>ROE: %{color:.1f}%<extra></extra>",
    marker=dict(cornerradius=5),
    textfont=dict(size=11, color="white"),
)
fig_tree.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", font_color="#E2E8F0",
    margin=dict(t=10, b=10, l=0, r=0), height=520,
    coloraxis_colorbar=dict(title="ROE %", tickfont=dict(color="#E2E8F0"), title_font=dict(color="#E2E8F0")),
)
st.plotly_chart(fig_tree, use_container_width=True, key="capital_treemap")

# ── Pattern detail explorer ────────────────────────────────────────────────────
st.markdown('<div class="section-header">🔍 Pattern Deep Dive</div>', unsafe_allow_html=True)

patterns = sorted(merged["capital_pattern"].dropna().unique().tolist())
selected_pattern = st.selectbox("Select Capital Allocation Pattern:", patterns, key="capital_pattern_sel")

pattern_companies = merged[merged["capital_pattern"] == selected_pattern].copy()

if pattern_companies.empty:
    st.info("No companies in this pattern.")
else:
    # Pattern stats
    p_cols = st.columns(4)
    with p_cols[0]:
        st.metric("Companies", len(pattern_companies))
    with p_cols[1]:
        st.metric("Avg ROE %", f"{pattern_companies['roe'].mean():.1f}%")
    with p_cols[2]:
        st.metric("Avg D/E", f"{pattern_companies['de'].mean():.2f}x")
    with p_cols[3]:
        st.metric("Total Mkt Cap", f"₹{pattern_companies['market_cap'].sum():,.0f} Cr")

    st.markdown("<br>", unsafe_allow_html=True)
    display = pattern_companies[["ticker","name","sector","roe","de","dividend_yield","fcf","market_cap"]].copy()
    display.columns = ["Ticker","Company","Sector","ROE %","D/E","Div Yield %","FCF (₹Cr)","Mkt Cap (₹Cr)"]
    for col in ["ROE %","Div Yield %"]:
        display[col] = display[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
    display["D/E"] = display["D/E"].apply(lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A")
    display["FCF (₹Cr)"] = display["FCF (₹Cr)"].apply(lambda x: f"₹{x:,.0f}" if pd.notna(x) else "N/A")
    display["Mkt Cap (₹Cr)"] = display["Mkt Cap (₹Cr)"].apply(lambda x: f"₹{x:,.0f}" if pd.notna(x) else "N/A")

    st.dataframe(display, use_container_width=True, hide_index=True, height=350)

# ── Pattern description cards ──────────────────────────────────────────────────
st.markdown('<div class="section-header">📖 Pattern Definitions</div>', unsafe_allow_html=True)

PATTERN_DESCRIPTIONS = {
    "Dividend Champions":   "Companies that consistently return high dividends — typically mature, cash-generative businesses.",
    "Growth Reinvestors":   "Companies that reinvest most FCF back into the business for high revenue/earnings growth.",
    "Debt Reducers":        "Companies actively deleveraging — reducing debt-to-equity year-over-year.",
    "Cash Hoarders":        "Companies with large cash reserves relative to market cap — often waiting for M&A opportunity.",
    "Acquirers":            "Companies growing through strategic acquisitions — M&A activity as a core capital strategy.",
    "Buyback Kings":        "Companies with large share repurchase programs — returning capital via buybacks vs dividends.",
    "Capex Heavy":          "High capital expenditure intensity — typically in infrastructure, energy, or manufacturing.",
    "Balanced Allocators":  "Well-balanced capital deployment across dividends, capex, debt repayment, and buybacks.",
}

desc_cols = st.columns(2)
for i, (pat, desc) in enumerate(PATTERN_DESCRIPTIONS.items()):
    with desc_cols[i % 2]:
        count = len(merged[merged["capital_pattern"] == pat])
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
                    border-radius:12px;padding:14px 16px;margin-bottom:10px;">
            <div style="font-weight:600;color:#E2E8F0;font-size:0.9rem;">{pat}
                <span style="background:rgba(124,58,237,0.2);color:#A78BFA;border-radius:10px;
                             padding:2px 8px;font-size:0.75rem;margin-left:6px;">{count} cos</span>
            </div>
            <div style="color:rgba(226,232,240,0.6);font-size:0.82rem;margin-top:6px;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
