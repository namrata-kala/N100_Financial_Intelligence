"""
src/dashboard/app.py
Main Streamlit entry point for Nifty 100 Analytics Dashboard.
Run with: streamlit run src/dashboard/app.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "**Nifty 100 Financial Intelligence Dashboard** — Sprint 4",
    },
)

# ─── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Base */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Background */
.stApp { background: linear-gradient(135deg, #0F0F1A 0%, #1A1A2E 50%, #16213E 100%); }

/* Sidebar */
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(255,255,255,0.08);
}

/* KPI Cards */
.kpi-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 16px;
    padding: 20px 24px;
    text-align: center;
    backdrop-filter: blur(8px);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 32px rgba(124,58,237,0.25);
}
.kpi-label {
    font-size: 0.75rem;
    font-weight: 500;
    color: rgba(226,232,240,0.6);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
}
.kpi-value {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #7C3AED, #06B6D4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.kpi-sub {
    font-size: 0.72rem;
    color: rgba(226,232,240,0.45);
    margin-top: 4px;
}

/* Section headers */
.section-header {
    font-size: 1.3rem;
    font-weight: 600;
    color: #E2E8F0;
    padding: 12px 0 4px 0;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 16px;
}

/* Badges */
.badge-green, .badge-red, .badge-yellow, .badge-blue {
    display: inline-block;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.8rem;
    margin: 3px 2px;
}
.badge-green { background: rgba(16,185,129,0.15); color: #10B981; border: 1px solid rgba(16,185,129,0.3); }
.badge-red { background: rgba(239,68,68,0.15); color: #EF4444; border: 1px solid rgba(239,68,68,0.3); }
.badge-yellow { background: rgba(245,158,11,0.15); color: #F59E0B; border: 1px solid rgba(245,158,11,0.3); }
.badge-blue { background: rgba(6,182,212,0.15); color: #06B6D4; border: 1px solid rgba(6,182,212,0.3); }

/* Company card */
.company-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(124,58,237,0.3);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
}
.company-name { font-size: 1.6rem; font-weight: 700; color: #E2E8F0; }
.company-ticker { font-size: 1rem; color: #7C3AED; font-weight: 600; }

/* DataFrames */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #7C3AED, #4F46E5);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(124,58,237,0.4);
}

/* Preset buttons row */
.preset-btn button {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #E2E8F0 !important;
    font-size: 0.8rem !important;
}

/* Header logo area */
.dashboard-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 0 20px 0;
}
.dashboard-title {
    font-size: 1.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, #7C3AED, #06B6D4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
</style>
""", unsafe_allow_html=True)

# ─── Sidebar nav header ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 16px 0 24px 0;">
        <div style="font-size:2rem;">📊</div>
        <div style="font-size:1.1rem; font-weight:700; background:linear-gradient(135deg,#7C3AED,#06B6D4);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                    background-clip:text;">Nifty 100</div>
        <div style="font-size:0.7rem; color:rgba(226,232,240,0.5); letter-spacing:0.1em;">
            ANALYTICS DASHBOARD
        </div>
    </div>
    <hr style="border:none; border-top:1px solid rgba(255,255,255,0.08); margin:0 0 16px 0;">
    """, unsafe_allow_html=True)

# ─── Landing content ──────────────────────────────────────────────────────────
st.markdown("""
<div class="dashboard-header">
    <span style="font-size:2.5rem;">📊</span>
    <div>
        <div class="dashboard-title">Nifty 100 Financial Intelligence Dashboard</div>
        <div style="color:rgba(226,232,240,0.5); font-size:0.85rem;">
            Sprint 4 · 92 Companies · 10 Years of Data · Real-time Analytics
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.info("👈 **Use the sidebar** to navigate between the 8 analytics screens.")
with col2:
    st.success("📈 **8 Screens**: Home · Profile · Screener · Peers · Trends · Sectors · Capital · Reports")
with col3:
    st.warning("⚡ All data cached for **10 minutes** for fast performance.")

st.markdown("""
<br>
<div style="display:grid; grid-template-columns:repeat(4,1fr); gap:16px;">
    <div class="kpi-card">
        <div class="kpi-label">Companies Tracked</div>
        <div class="kpi-value">92</div>
        <div class="kpi-sub">Nifty 100 Universe</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-label">Years of Data</div>
        <div class="kpi-value">10</div>
        <div class="kpi-sub">2015 – 2024</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-label">Sectors Covered</div>
        <div class="kpi-value">11</div>
        <div class="kpi-sub">BSE Sector Classification</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-label">Metrics Per Company</div>
        <div class="kpi-value">20+</div>
        <div class="kpi-sub">Financial Ratios & Indicators</div>
    </div>
</div>
""", unsafe_allow_html=True)