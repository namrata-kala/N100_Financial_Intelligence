"""
pages/01_home.py
Home Screen — Nifty 100 Analytics Dashboard
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from dashboard.utils.db import get_home_kpis, get_sectors, get_top_companies, get_companies

st.set_page_config(page_title="Home · Nifty 100", layout="wide", initial_sidebar_state="expanded")

# ── Load shared CSS ────────────────────────────────────────────────────────────
def load_css():
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html,body,[class*="css"]{font-family:'Inter',sans-serif;}
    .stApp{background:linear-gradient(135deg,#0F0F1A 0%,#1A1A2E 50%,#16213E 100%);}
    [data-testid="stSidebar"]{background:rgba(255,255,255,0.04);backdrop-filter:blur(10px);border-right:1px solid rgba(255,255,255,0.08);}
    .kpi-card{background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.10);border-radius:16px;padding:20px 24px;text-align:center;backdrop-filter:blur(8px);transition:transform 0.2s ease,box-shadow 0.2s ease;}
    .kpi-card:hover{transform:translateY(-3px);box-shadow:0 8px 32px rgba(124,58,237,0.25);}
    .kpi-label{font-size:0.75rem;font-weight:500;color:rgba(226,232,240,0.6);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;}
    .kpi-value{font-size:2rem;font-weight:700;background:linear-gradient(135deg,#7C3AED,#06B6D4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
    .kpi-sub{font-size:0.72rem;color:rgba(226,232,240,0.45);margin-top:4px;}
    .section-header{font-size:1.2rem;font-weight:600;color:#E2E8F0;padding:16px 0 8px 0;border-bottom:1px solid rgba(255,255,255,0.08);margin-bottom:16px;}
    </style>""", unsafe_allow_html=True)

load_css()

# ── Sidebar year selector ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏠 Home Controls")
    selected_year = st.selectbox("📅 Select Year", list(range(2024, 2018, -1)), index=0)

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:8px 0 24px 0;">
    <h1 style="font-size:2rem;font-weight:700;color:#E2E8F0;margin:0;">🏠 Market Overview</h1>
    <p style="color:rgba(226,232,240,0.5);margin:4px 0 0 0;">Nifty 100 Universe · Aggregate Intelligence</p>
</div>
""", unsafe_allow_html=True)

# ── KPI tiles ──────────────────────────────────────────────────────────────────
kpis = get_home_kpis(year=selected_year)

cols = st.columns(6)
kpi_configs = [
    ("avg_roe",        "Avg ROE",              "%",    "Return on Equity"),
    ("median_pe",      "Median P/E",            "x",    "Price-to-Earnings"),
    ("median_de",      "Median D/E",            "x",    "Debt-to-Equity"),
    ("total_companies","Total Companies",       "",     "Nifty 100 Universe"),
    ("median_rev_cagr","Rev CAGR 5Yr",          "%",    "Median Revenue CAGR"),
    ("debt_free_count","Debt-Free Cos",         "",     "Zero Net Debt"),
]

for col, (key, label, unit, sub) in zip(cols, kpi_configs):
    val = kpis.get(key, "N/A")
    val_str = f"{val}{unit}" if val != "N/A" else "N/A"
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{val_str}</div>
            <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts row ─────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1.4])

with col_left:
    st.markdown('<div class="section-header">🍩 Sector Breakdown</div>', unsafe_allow_html=True)
    sectors = get_sectors()
    if not sectors.empty:
        fig_donut = px.pie(
            sectors, values="company_count", names="sector",
            hole=0.6,
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_donut.update_traces(
            textposition="outside", textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Companies: %{value}<br>Share: %{percent}<extra></extra>",
        )
        fig_donut.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E2E8F0", showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10), height=340,
            annotations=[dict(text=f"<b>{int(sectors['company_count'].sum())}</b><br>Companies",
                              x=0.5, y=0.5, font_size=16, showarrow=False, font_color="#E2E8F0")],
        )
        st.plotly_chart(fig_donut, use_container_width=True, key="home_donut")

with col_right:
    st.markdown('<div class="section-header">🏆 Top 5 by Composite Quality Score</div>', unsafe_allow_html=True)
    top5 = get_top_companies(year=selected_year, n=5)
    if not top5.empty:
        display = top5[["ticker","name","sector","composite_score","roe","roce","pe","opm"]].copy()
        display.columns = ["Ticker","Company","Sector","Quality Score","ROE %","ROCE %","P/E","OPM %"]
        display["Quality Score"] = display["Quality Score"].apply(lambda x: f"⭐ {x:.1f}" if pd.notnull(x) else "N/A")
        display["ROE %"] = display["ROE %"].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "N/A")
        display["ROCE %"] = display["ROCE %"].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "N/A")
        display["P/E"]  = display["P/E"].apply(lambda x: f"{x:.1f}x" if pd.notnull(x) else "N/A")
        display["OPM %"] = display["OPM %"].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "N/A")
        st.dataframe(display, use_container_width=True, hide_index=True, height=200)

        # Bar chart for composite scores
        fig_bar = px.bar(
            top5, x="name", y="composite_score",
            color="composite_score",
            color_continuous_scale=["#4F46E5","#7C3AED","#06B6D4"],
            labels={"composite_score": "Quality Score", "name": ""},
            text="composite_score",
        )
        fig_bar.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E2E8F0", showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10), height=200,
            coloraxis_showscale=False,
            xaxis=dict(tickfont=dict(size=10)),
        )
        st.plotly_chart(fig_bar, use_container_width=True, key="home_topbar")

st.markdown("<br>", unsafe_allow_html=True)

# ── Sector market cap bar ──────────────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Sector Market Cap & Average ROE</div>', unsafe_allow_html=True)
sectors_df = get_sectors()
if not sectors_df.empty:
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        name="Market Cap (₹ Cr)",
        x=sectors_df["sector"], y=sectors_df["total_market_cap"],
        marker_color="#7C3AED", opacity=0.85,
        yaxis="y1",
    ))
    fig2.add_trace(go.Scatter(
        name="Avg ROE %",
        x=sectors_df["sector"], y=sectors_df["avg_roe"],
        mode="lines+markers+text",
        line=dict(color="#06B6D4", width=2.5),
        marker=dict(size=8, color="#06B6D4"),
        yaxis="y2",
        text=[f"{v:.1f}%" for v in sectors_df["avg_roe"]],
        textposition="top center",
        textfont=dict(size=10, color="#06B6D4"),
    ))
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E2E8F0",
        yaxis=dict(title="Market Cap (₹ Cr)", gridcolor="rgba(255,255,255,0.05)"),
        yaxis2=dict(title="Avg ROE %", overlaying="y", side="right",
                    gridcolor="rgba(255,255,255,0.0)", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=40, b=60), height=380,
        hovermode="x unified",
    )
    st.plotly_chart(fig2, use_container_width=True, key="home_sector_bar")
