"""
pages/03_screener.py
Stock Screener Screen — Nifty 100 Analytics Dashboard
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import pandas as pd
import io

from dashboard.utils.db import get_all_ratios_year

st.set_page_config(page_title="Screener · Nifty 100", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:linear-gradient(135deg,#0F0F1A 0%,#1A1A2E 50%,#16213E 100%);}
[data-testid="stSidebar"]{background:rgba(255,255,255,0.04);backdrop-filter:blur(10px);border-right:1px solid rgba(255,255,255,0.08);}
.section-header{font-size:1.2rem;font-weight:600;color:#E2E8F0;padding:16px 0 8px 0;border-bottom:1px solid rgba(255,255,255,0.08);margin-bottom:16px;}
.stButton>button{background:linear-gradient(135deg,#7C3AED,#4F46E5);color:white;border:none;border-radius:8px;font-weight:500;}
.result-count{background:rgba(124,58,237,0.15);border:1px solid rgba(124,58,237,0.3);border-radius:12px;padding:10px 20px;font-size:1rem;font-weight:600;color:#A78BFA;display:inline-block;margin-bottom:16px;}
</style>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Presets
# ─────────────────────────────────────────────────────────────────────────────
PRESETS = {
    "Quality":   {"roe_min":18, "de_max":0.5, "fcf_min":0, "rev_cagr_min":12, "pat_cagr_min":10, "opm_min":18, "pe_max":50, "pb_max":10, "div_min":0, "icr_min":5},
    "Value":     {"roe_min":10, "de_max":1.5, "fcf_min":0, "rev_cagr_min":5,  "pat_cagr_min":5,  "opm_min":10, "pe_max":15, "pb_max":3,  "div_min":1, "icr_min":2},
    "Growth":    {"roe_min":15, "de_max":1.0, "fcf_min":0, "rev_cagr_min":20, "pat_cagr_min":20, "opm_min":15, "pe_max":80, "pb_max":10, "div_min":0, "icr_min":3},
    "Dividend":  {"roe_min":10, "de_max":1.0, "fcf_min":0, "rev_cagr_min":5,  "pat_cagr_min":5,  "opm_min":10, "pe_max":30, "pb_max":8,  "div_min":2, "icr_min":3},
    "Debt-Free": {"roe_min":0,  "de_max":0.1, "fcf_min":0, "rev_cagr_min":0,  "pat_cagr_min":0,  "opm_min":0,  "pe_max":100,"pb_max":50, "div_min":0, "icr_min":0},
    "Turnaround":{"roe_min":5,  "de_max":3.0, "fcf_min":-500,"rev_cagr_min":5,"pat_cagr_min":-5, "opm_min":5,  "pe_max":30, "pb_max":5,  "div_min":0, "icr_min":1},
}

# Session state for filter values
if "filters" not in st.session_state:
    st.session_state.filters = {
        "roe_min": 0.0, "de_max": 10.0, "fcf_min": -1000.0, "rev_cagr_min": 0.0,
        "pat_cagr_min": 0.0, "opm_min": 0.0, "pe_max": 120.0, "pb_max": 50.0,
        "div_min": 0.0, "icr_min": 0.0,
    }

# ── Sidebar filters ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Screener Filters")

    # Preset buttons
    st.markdown("**⚡ Quick Presets**")
    preset_cols = st.columns(2)
    for i, preset_name in enumerate(PRESETS.keys()):
        with preset_cols[i % 2]:
            if st.button(preset_name, key=f"preset_{preset_name}", use_container_width=True):
                st.session_state.filters = PRESETS[preset_name].copy()
                st.rerun()

    st.markdown("---")
    st.markdown("**🎛️ Custom Filters**")

    f = st.session_state.filters
    roe_min      = st.slider("ROE Min (%)",          0.0,  60.0, float(f["roe_min"]),      0.5, key="sl_roe")
    de_max       = st.slider("D/E Max (x)",          0.0,  10.0, float(f["de_max"]),       0.1, key="sl_de")
    fcf_min      = st.slider("FCF Min (₹ Cr)",    -1000.0,5000.0,float(f["fcf_min"]),     100.0,key="sl_fcf")
    rev_cagr_min = st.slider("Revenue CAGR Min (%)", 0.0,  30.0, float(f["rev_cagr_min"]),0.5, key="sl_revcagr")
    pat_cagr_min = st.slider("PAT CAGR Min (%)",   -10.0, 40.0, float(f["pat_cagr_min"]), 0.5, key="sl_patcagr")
    opm_min      = st.slider("OPM Min (%)",          0.0,  50.0, float(f["opm_min"]),      0.5, key="sl_opm")
    pe_max       = st.slider("P/E Max (x)",          1.0, 120.0, float(f["pe_max"]),       1.0, key="sl_pe")
    pb_max       = st.slider("P/B Max (x)",          0.5,  50.0, float(f["pb_max"]),       0.5, key="sl_pb")
    div_min      = st.slider("Dividend Yield Min (%)",0.0, 10.0, float(f["div_min"]),      0.1, key="sl_div")
    icr_min      = st.slider("ICR Min (x)",          0.0,  30.0, float(f["icr_min"]),      0.5, key="sl_icr")

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:8px 0 24px 0;">
    <h1 style="font-size:2rem;font-weight:700;color:#E2E8F0;margin:0;">🔍 Stock Screener</h1>
    <p style="color:rgba(226,232,240,0.5);margin:4px 0 0 0;">Filter 92 Nifty 100 companies by financial metrics</p>
</div>
""", unsafe_allow_html=True)

# ── Load & filter data ─────────────────────────────────────────────────────────
df = get_all_ratios_year(year=2024)

# Apply filters
mask = (
    (df["roe"]              >= roe_min) &
    (df["de"]               <= de_max) &
    (df["fcf"]              >= fcf_min) &
    (df["revenue_cagr_5yr"] >= rev_cagr_min) &
    (df["pat_cagr_5yr"]     >= pat_cagr_min) &
    (df["opm"]              >= opm_min) &
    (df["pe"]               <= pe_max) &
    (df["pb"]               <= pb_max) &
    (df["dividend_yield"]   >= div_min) &
    (df["icr"]              >= icr_min)
)
result = df[mask].copy()

# ── Result count ───────────────────────────────────────────────────────────────
st.markdown(f'<div class="result-count">🎯 {len(result)} companies match your filters</div>', unsafe_allow_html=True)

# ── Results table ──────────────────────────────────────────────────────────────
if result.empty:
    st.info("No companies match the current filters. Try relaxing the criteria.")
else:
    display = result[[
        "ticker","name","sector","composite_score",
        "roe","roce","pe","pb","de","opm","npm",
        "revenue_cagr_5yr","pat_cagr_5yr","dividend_yield","icr","fcf"
    ]].copy()
    display.columns = [
        "Ticker","Company","Sector","Quality Score",
        "ROE %","ROCE %","P/E","P/B","D/E","OPM %","NPM %",
        "Rev CAGR %","PAT CAGR %","Div Yield %","ICR","FCF (₹Cr)"
    ]

    # Format numbers
    for col in ["ROE %","ROCE %","OPM %","NPM %","Rev CAGR %","PAT CAGR %","Div Yield %"]:
        display[col] = display[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
    for col in ["P/E","P/B","D/E","ICR"]:
        display[col] = display[col].apply(lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A")
    display["Quality Score"] = display["Quality Score"].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
    display["FCF (₹Cr)"] = display["FCF (₹Cr)"].apply(lambda x: f"₹{x:,.0f}" if pd.notna(x) else "N/A")

    st.dataframe(display, use_container_width=True, hide_index=True, height=420)

    # ── CSV download ───────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    csv_buf = io.StringIO()
    result.to_csv(csv_buf, index=False)
    st.download_button(
        label="⬇️ Download CSV",
        data=csv_buf.getvalue(),
        file_name=f"nifty100_screener_{len(result)}_companies.csv",
        mime="text/csv",
        key="screener_csv_download",
    )
