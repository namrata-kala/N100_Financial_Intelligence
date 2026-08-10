"""
pages/06_sectors.py
Sector Analysis Screen — Nifty 100 Analytics Dashboard
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from dashboard.utils.db import get_sector_bubble, get_sectors

st.set_page_config(page_title="Sector Analysis · Nifty 100", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:linear-gradient(135deg,#0F0F1A 0%,#1A1A2E 50%,#16213E 100%);}
[data-testid="stSidebar"]{background:rgba(255,255,255,0.04);backdrop-filter:blur(10px);border-right:1px solid rgba(255,255,255,0.08);}
.section-header{font-size:1.2rem;font-weight:600;color:#E2E8F0;padding:16px 0 8px 0;border-bottom:1px solid rgba(255,255,255,0.08);margin-bottom:16px;}
.kpi-card{background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.10);border-radius:16px;padding:16px;text-align:center;}
.kpi-label{font-size:0.7rem;font-weight:500;color:rgba(226,232,240,0.6);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;}
.kpi-value{font-size:1.5rem;font-weight:700;background:linear-gradient(135deg,#7C3AED,#06B6D4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
</style>""", unsafe_allow_html=True)

# ── Data ───────────────────────────────────────────────────────────────────────
bubble_df  = get_sector_bubble(year=2024)
sectors_df = get_sectors()

all_sectors = sorted(bubble_df["sector"].dropna().unique().tolist())

with st.sidebar:
    st.markdown("### 🏭 Sector Analysis")
    selected_sector = st.selectbox("🔎 Select Sector", ["All Sectors"] + all_sectors)

st.markdown(f"""
<div style="padding:8px 0 24px 0;">
    <h1 style="font-size:2rem;font-weight:700;color:#E2E8F0;margin:0;">🏭 Sector Analysis</h1>
    <p style="color:rgba(226,232,240,0.5);margin:4px 0 0 0;">
        {'All Sectors' if selected_sector == 'All Sectors' else f'Deep dive: <strong style="color:#7C3AED">{selected_sector}</strong>'}
    </p>
</div>
""", unsafe_allow_html=True)

# ── Filter ─────────────────────────────────────────────────────────────────────
plot_df = bubble_df if selected_sector == "All Sectors" else bubble_df[bubble_df["sector"] == selected_sector]

# ── Sector KPI summary cards ───────────────────────────────────────────────────
if selected_sector != "All Sectors":
    sec_data = sectors_df[sectors_df["sector"] == selected_sector]
    if not sec_data.empty:
        s = sec_data.iloc[0]
        kpi_cols = st.columns(5)
        kpis = [
            ("Companies", str(int(s["company_count"])), ""),
            ("Avg ROE", f"{s['avg_roe']:.1f}%", ""),
            ("Avg P/E", f"{s['avg_pe']:.1f}x", ""),
            ("Avg OPM", f"{s['avg_opm']:.1f}%", ""),
            ("Avg Rev CAGR", f"{s['avg_rev_cagr']:.1f}%", ""),
        ]
        for col, (lbl, val, _) in zip(kpi_cols, kpis):
            with col:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">{lbl}</div>
                    <div class="kpi-value">{val}</div>
                </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

# ── Bubble chart ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🫧 Bubble Chart — Revenue vs ROE (size = Market Cap)</div>', unsafe_allow_html=True)

if plot_df.empty:
    st.warning("No data available for selected sector.")
else:
    # Clip market cap to avoid extreme bubbles
    plot_df = plot_df.copy()
    plot_df["mkt_cap_size"] = plot_df["market_cap"].clip(upper=plot_df["market_cap"].quantile(0.95))

    fig_bubble = px.scatter(
        plot_df,
        x="revenue", y="roe",
        size="mkt_cap_size",
        color="sub_sector" if selected_sector != "All Sectors" else "sector",
        hover_name="name",
        hover_data={"ticker": True, "revenue": ":.0f", "roe": ":.1f", "market_cap": ":.0f", "mkt_cap_size": False},
        labels={"revenue":"Revenue (₹ Cr)", "roe":"ROE %", "market_cap":"Market Cap (₹ Cr)"},
        size_max=55,
        color_discrete_sequence=px.colors.qualitative.Bold,
        opacity=0.82,
    )
    fig_bubble.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E2E8F0",
        xaxis=dict(title="Revenue (₹ Cr)", gridcolor="rgba(255,255,255,0.06)"),
        yaxis=dict(title="ROE %", gridcolor="rgba(255,255,255,0.06)"),
        legend=dict(title="Sector" if selected_sector == "All Sectors" else "Sub-Sector",
                    font=dict(size=10)),
        margin=dict(t=30, b=40), height=480,
        hovermode="closest",
    )
    st.plotly_chart(fig_bubble, use_container_width=True, key="sectors_bubble")

# ── Sector median KPI bar chart ────────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Sector Median KPI Comparison</div>', unsafe_allow_html=True)

metric_choice = st.radio(
    "Select metric to compare:",
    ["avg_roe","avg_pe","avg_opm","avg_rev_cagr"],
    format_func=lambda x: {"avg_roe":"Avg ROE %","avg_pe":"Avg P/E","avg_opm":"Avg OPM %","avg_rev_cagr":"Avg Rev CAGR %"}[x],
    horizontal=True,
    key="sector_metric_radio",
)

if not sectors_df.empty:
    highlight = sectors_df["sector"] == selected_sector if selected_sector != "All Sectors" else pd.Series([True]*len(sectors_df))
    bar_colors = ["#7C3AED" if h else "#2D2D4A" for h in highlight]

    fig_bar = go.Figure(go.Bar(
        x=sectors_df["sector"], y=sectors_df[metric_choice],
        marker_color=bar_colors,
        text=sectors_df[metric_choice].apply(lambda v: f"{v:.1f}"),
        textposition="outside",
    ))
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E2E8F0",
        xaxis=dict(tickangle=-30, tickfont=dict(size=10), gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
        margin=dict(t=30, b=80), height=320,
        showlegend=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True, key="sectors_kpi_bar")
