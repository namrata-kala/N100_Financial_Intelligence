"""
pages/04_peers.py
Peer Comparison Screen — Nifty 100 Analytics Dashboard
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from dashboard.utils.db import get_peers, get_all_peer_groups, get_companies

st.set_page_config(page_title="Peer Comparison · Nifty 100", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:linear-gradient(135deg,#0F0F1A 0%,#1A1A2E 50%,#16213E 100%);}
[data-testid="stSidebar"]{background:rgba(255,255,255,0.04);backdrop-filter:blur(10px);border-right:1px solid rgba(255,255,255,0.08);}
.section-header{font-size:1.2rem;font-weight:600;color:#E2E8F0;padding:16px 0 8px 0;border-bottom:1px solid rgba(255,255,255,0.08);margin-bottom:16px;}
</style>""", unsafe_allow_html=True)

# ── Sidebar controls ───────────────────────────────────────────────────────────
peer_groups = get_all_peer_groups()
all_companies = get_companies()

with st.sidebar:
    st.markdown("### 👥 Peer Comparison")
    selected_group = st.selectbox("📂 Select Peer Group", peer_groups)
    peers_df = get_peers(selected_group)

    if not peers_df.empty:
        company_options = peers_df["ticker"].tolist()
        selected_ticker = st.selectbox("🎯 Benchmark Company", company_options)
    else:
        selected_ticker = None

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="padding:8px 0 24px 0;">
    <h1 style="font-size:2rem;font-weight:700;color:#E2E8F0;margin:0;">👥 Peer Comparison</h1>
    <p style="color:rgba(226,232,240,0.5);margin:4px 0 0 0;">Group: <strong style="color:#7C3AED">{selected_group}</strong></p>
</div>
""", unsafe_allow_html=True)

if peers_df.empty:
    st.warning("No data available for this peer group.")
    st.stop()

# ── Radar chart ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🕸️ Radar Chart — Benchmark vs Peer Average</div>', unsafe_allow_html=True)

RADAR_METRICS = ["roe","roce","opm","npm","revenue_cagr_5yr","composite_score","dividend_yield","pe"]
RADAR_LABELS  = ["ROE %","ROCE %","OPM %","NPM %","Rev CAGR %","Quality","Div Yield","P/E (inv)"]

peer_avg = peers_df[RADAR_METRICS].mean()

if selected_ticker and selected_ticker in peers_df["ticker"].values:
    bench = peers_df[peers_df["ticker"] == selected_ticker][RADAR_METRICS].iloc[0]
else:
    bench = peer_avg

# Normalize 0-100 using peer min-max
def norm_series(s: pd.Series) -> pd.Series:
    lo, hi = s.min(), s.max()
    if hi == lo:
        return pd.Series([50.0] * len(s), index=s.index)
    return (s - lo) / (hi - lo) * 100

norm_avg   = norm_series(peer_avg)
norm_bench = pd.Series({m: norm_series(peers_df[m])[peers_df["ticker"] == selected_ticker].values[0]
                         if selected_ticker and selected_ticker in peers_df["ticker"].values
                         else norm_series(peers_df[m]).mean()
                         for m in RADAR_METRICS})

# Invert P/E (lower is better)
norm_avg["pe"]   = 100 - norm_avg["pe"]
norm_bench["pe"] = 100 - norm_bench["pe"]

fig_radar = go.Figure()
# Peer average
fig_radar.add_trace(go.Scatterpolar(
    r=list(norm_avg.values) + [norm_avg.values[0]],
    theta=RADAR_LABELS + [RADAR_LABELS[0]],
    fill="toself", fillcolor="rgba(6,182,212,0.1)",
    line=dict(color="#06B6D4", width=2),
    name="Peer Average",
))
# Benchmark
fig_radar.add_trace(go.Scatterpolar(
    r=list(norm_bench.values) + [norm_bench.values[0]],
    theta=RADAR_LABELS + [RADAR_LABELS[0]],
    fill="toself", fillcolor="rgba(124,58,237,0.15)",
    line=dict(color="#7C3AED", width=2.5),
    name=selected_ticker or "Benchmark",
))
fig_radar.update_layout(
    polar=dict(
        bgcolor="rgba(0,0,0,0)",
        radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255,255,255,0.1)",
                        tickfont=dict(color="rgba(226,232,240,0.4)", size=9)),
        angularaxis=dict(gridcolor="rgba(255,255,255,0.08)", tickfont=dict(color="#E2E8F0", size=11)),
    ),
    paper_bgcolor="rgba(0,0,0,0)", font_color="#E2E8F0",
    legend=dict(orientation="h", yanchor="bottom", y=-0.15, x=0.5, xanchor="center"),
    margin=dict(t=40, b=80), height=440,
)
st.plotly_chart(fig_radar, use_container_width=True, key="peers_radar")

# ── KPI comparison table ───────────────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Side-by-Side KPI Comparison</div>', unsafe_allow_html=True)

display_cols = ["ticker","name","roe","roce","pe","pb","de","opm","npm",
                "revenue_cagr_5yr","dividend_yield","composite_score","market_cap"]
display_df = peers_df[display_cols].copy()
display_df.columns = ["Ticker","Company","ROE %","ROCE %","P/E","P/B","D/E",
                       "OPM %","NPM %","Rev CAGR %","Div Yield %","Quality Score","Mkt Cap (₹Cr)"]

# Format
for col in ["ROE %","ROCE %","OPM %","NPM %","Rev CAGR %","Div Yield %"]:
    display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
for col in ["P/E","P/B","D/E"]:
    display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A")
display_df["Quality Score"] = display_df["Quality Score"].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
display_df["Mkt Cap (₹Cr)"] = display_df["Mkt Cap (₹Cr)"].apply(lambda x: f"₹{x:,.0f}" if pd.notna(x) else "N/A")

# Highlight benchmark row
def highlight_bench(row):
    if row["Ticker"] == selected_ticker:
        return ["background-color: rgba(124,58,237,0.2); font-weight:bold"] * len(row)
    return [""] * len(row)

styled = display_df.style.apply(highlight_bench, axis=1)
st.dataframe(styled, use_container_width=True, hide_index=True, height=400)
