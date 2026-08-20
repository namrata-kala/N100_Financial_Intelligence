"""
pages/05_trends.py
Trend Analysis Screen — Nifty 100 Analytics Dashboard
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from dashboard.utils.db import get_companies, get_ratios, get_pl, get_cf

st.set_page_config(page_title="Trend Analysis · Nifty 100", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:linear-gradient(135deg,#0F0F1A 0%,#1A1A2E 50%,#16213E 100%);}
[data-testid="stSidebar"]{background:rgba(255,255,255,0.04);backdrop-filter:blur(10px);border-right:1px solid rgba(255,255,255,0.08);}
.section-header{font-size:1.2rem;font-weight:600;color:#E2E8F0;padding:16px 0 8px 0;border-bottom:1px solid rgba(255,255,255,0.08);margin-bottom:16px;}
</style>""", unsafe_allow_html=True)

METRIC_MAP = {
    "Revenue (₹ Cr)":     ("pl", "revenue"),
    "Net Profit (₹ Cr)":  ("pl", "pat"),
    "EBITDA (₹ Cr)":      ("pl", "ebitda"),
    "ROE %":              ("ratios", "roe"),
    "ROCE %":             ("ratios", "roce"),
    "OPM %":              ("ratios", "opm"),
    "NPM %":              ("ratios", "npm"),
    "P/E":                ("ratios", "pe"),
    "D/E":                ("ratios", "de"),
    "FCF (₹ Cr)":         ("cf", "fcf"),
}

companies = get_companies()
ticker_opts = [f"{r.ticker} — {r.name}" for r in companies.itertuples()]

with st.sidebar:
    st.markdown("### 📈 Trend Analysis")
    search = st.selectbox("🔍 Select Company", ticker_opts)
    selected_metrics = st.multiselect(
        "📊 Select Metrics (max 3)",
        list(METRIC_MAP.keys()),
        default=["Revenue (₹ Cr)", "Net Profit (₹ Cr)", "ROE %"],
        max_selections=3,
    )

ticker = search.split(" — ")[0].strip()

st.markdown(f"""
<div style="padding:8px 0 24px 0;">
    <h1 style="font-size:2rem;font-weight:700;color:#E2E8F0;margin:0;">📈 Trend Analysis</h1>
    <p style="color:rgba(226,232,240,0.5);margin:4px 0 0 0;">10-year financial trend with YoY % change · <strong style="color:#7C3AED">{ticker}</strong></p>
</div>
""", unsafe_allow_html=True)

if not selected_metrics:
    st.info("Select at least one metric from the sidebar.")
    st.stop()

# ── Fetch data ─────────────────────────────────────────────────────────────────
ratios_df = get_ratios(ticker)
pl_df     = get_pl(ticker)
cf_df     = get_cf(ticker)

source_map = {"pl": pl_df, "ratios": ratios_df, "cf": cf_df}

COLORS = ["#7C3AED", "#06B6D4", "#10B981"]

fig = go.Figure()

for i, metric_name in enumerate(selected_metrics):
    src_key, col = METRIC_MAP[metric_name]
    src_df = source_map[src_key]

    if src_df.empty or col not in src_df.columns:
        st.warning(f"No data for {metric_name}")
        continue

    values = src_df[col].values
    years  = src_df["year"].values

    # YoY % change
    yoy = [None] + [
        round((values[j] - values[j-1]) / abs(values[j-1]) * 100, 1) if values[j-1] != 0 else 0.0
        for j in range(1, len(values))
    ]

    color = COLORS[i % len(COLORS)]

    fig.add_trace(go.Scatter(
        name=metric_name,
        x=years, y=values,
        mode="lines+markers+text",
        line=dict(color=color, width=2.5),
        marker=dict(size=8, color=color),
        text=[f"<b>{y:+.1f}%</b>" if y is not None else "" for y in yoy],
        textposition="top center",
        textfont=dict(size=9, color=color),
        yaxis=f"y{i+1}" if i > 0 else "y",
        hovertemplate=f"<b>{metric_name}</b><br>Year: %{{x}}<br>Value: %{{y:,.1f}}<extra></extra>",
    ))

# Build multi-axis layout
layout_kwargs = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font_color="#E2E8F0",
    xaxis=dict(tickmode="linear", dtick=1, gridcolor="rgba(255,255,255,0.05)"),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=11)),
    margin=dict(t=60, b=40), height=480,
)

# Y-axes
axis_colors = ["#7C3AED", "#06B6D4", "#10B981"]
for i, m in enumerate(selected_metrics):
    axis_key = "yaxis" if i == 0 else f"yaxis{i+1}"
    overlay_key = None if i == 0 else "y"
    side = ["left","right","right"][i]
    layout_kwargs[axis_key] = dict(
        title=m, gridcolor="rgba(255,255,255,0.05)" if i == 0 else "rgba(0,0,0,0)",
        title_font=dict(color=axis_colors[i]),
        tickfont=dict(color=axis_colors[i]),
        showgrid=(i == 0),
        position=1.0 if i == 2 else None,
        **({"overlaying": "y", "side": side} if i > 0 else {}),
    )

fig.update_layout(**layout_kwargs)
st.plotly_chart(fig, use_container_width=True, key="trends_main_chart")

# ── YoY change summary table ───────────────────────────────────────────────────
st.markdown('<div class="section-header">📋 Year-on-Year Change Summary</div>', unsafe_allow_html=True)

summary_rows = []
for metric_name in selected_metrics:
    src_key, col = METRIC_MAP[metric_name]
    src_df = source_map[src_key]
    if src_df.empty or col not in src_df.columns:
        continue
    vals  = src_df[col].values
    years = src_df["year"].values
    for j in range(1, len(vals)):
        yoy_pct = round((vals[j] - vals[j-1]) / abs(vals[j-1]) * 100, 1) if vals[j-1] != 0 else 0.0
        summary_rows.append({
            "Metric": metric_name,
            "Year":   int(years[j]),
            "Value":  round(float(vals[j]), 2),
            "YoY Δ %": f"{'▲' if yoy_pct >= 0 else '▼'} {abs(yoy_pct):.1f}%",
        })

if summary_rows:
    summary_df = pd.DataFrame(summary_rows)
    pivot = summary_df.pivot_table(index="Year", columns="Metric", values="YoY Δ %", aggfunc="first")
    pivot = pivot.reset_index().sort_values("Year", ascending=False)
    st.dataframe(pivot, use_container_width=True, hide_index=True)
