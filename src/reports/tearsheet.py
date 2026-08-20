import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Configuration
DB_PATH = "data/nifty100.db"
CHARTS_DIR = "output/charts"
TEARSHEETS_DIR = "reports/tearsheets"
SECTOR_DIR = "reports/sector"
PORTFOLIO_DIR = "reports/portfolio"
PROS_CONS_FILE = "output/pros_cons_generated.csv"
CASHFLOW_FILE = "output/cashflow_intelligence.xlsx"

os.makedirs(CHARTS_DIR, exist_ok=True)
os.makedirs(TEARSHEETS_DIR, exist_ok=True)
os.makedirs(SECTOR_DIR, exist_ok=True)
os.makedirs(PORTFOLIO_DIR, exist_ok=True)

# Define styles
styles = getSampleStyleSheet()
title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, textColor=colors.whitesmoke)
subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, textColor=colors.lightgrey)
section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=14, textColor=colors.darkblue, spaceAfter=10)
pro_style = ParagraphStyle('Pro', parent=styles['Normal'], fontSize=10, textColor=colors.green, spaceAfter=5)
con_style = ParagraphStyle('Con', parent=styles['Normal'], fontSize=10, textColor=colors.red, spaceAfter=5)

def get_data(ticker):
    conn = sqlite3.connect(DB_PATH)
    company = pd.read_sql("SELECT * FROM companies WHERE ticker=?", conn, params=(ticker,)).iloc[0]
    cid = int(company['company_id'])
    pl = pd.read_sql("SELECT * FROM pl WHERE company_id=? ORDER BY year", conn, params=(cid,))
    bs = pd.read_sql("SELECT * FROM balance_sheet WHERE company_id=? ORDER BY year", conn, params=(cid,))
    cf = pd.read_sql("SELECT * FROM cash_flow WHERE company_id=? ORDER BY year", conn, params=(cid,))
    ratios = pd.read_sql("SELECT * FROM ratios WHERE company_id=? ORDER BY year", conn, params=(cid,))
    conn.close()
    
    # Pros Cons
    try:
        pc_df = pd.read_csv(PROS_CONS_FILE)
        pc = pc_df[pc_df['company_id'] == cid]
        pros = pc[pc['type'] == 'pro']['text'].tolist()
        cons = pc[pc['type'] == 'con']['text'].tolist()
    except:
        pros = ["Strong historical performance."]
        cons = ["Valuation appears stretched."]

    # Capital Allocation
    try:
        cfi_df = pd.read_excel(CASHFLOW_FILE)
        cfi = cfi_df[cfi_df['ticker'] == ticker].iloc[0]
        pattern = cfi['capital_pattern']
    except:
        pattern = company['capital_pattern']

    return {
        "company": company, "pl": pl, "bs": bs, "cf": cf, 
        "ratios": ratios, "pros": pros, "cons": cons, "pattern": pattern
    }

def draw_rev_pat_chart(pl, filename):
    plt.figure(figsize=(6, 3))
    x = np.arange(len(pl['year']))
    width = 0.35
    plt.bar(x - width/2, pl['revenue'], width, label='Revenue', color='#1f77b4')
    plt.bar(x + width/2, pl['pat'], width, label='Net Profit', color='#ff7f0e')
    plt.xticks(x, pl['year'], rotation=45)
    plt.legend()
    plt.title('Historical Revenue & Net Profit')
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def draw_roe_roce_chart(ratios, filename):
    plt.figure(figsize=(6, 3))
    plt.plot(ratios['year'], ratios['roe'], marker='o', label='ROE %', color='#2ca02c')
    plt.plot(ratios['year'], ratios['roce'], marker='s', label='ROCE %', color='#d62728')
    plt.xticks(ratios['year'], rotation=45)
    plt.legend()
    plt.title('ROE vs ROCE Trend')
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def draw_bs_composition(bs, filename):
    plt.figure(figsize=(6, 3))
    years = pd.to_numeric(bs["year"], errors="coerce")
    equity = pd.to_numeric(bs["total_equity"], errors="coerce").fillna(0)
    debt = pd.to_numeric(bs["total_debt"], errors="coerce").fillna(0)
    assets = pd.to_numeric(bs["total_assets"], errors="coerce").fillna(0)

    valid = years.notna()

    years = years[valid]
    equity = equity[valid]
    debt = debt[valid]
    assets = assets[valid]
    other_liab = (assets - equity - debt).clip(lower=0)

    plt.bar(years, equity, label='Equity', color='#9467bd')
    plt.bar(years, debt, bottom=equity, label='Borrowings', color='#8c564b')
    plt.bar(years, other_liab, bottom=equity+debt, label='Other Liab', color='#e377c2')
    
    plt.xticks(list(years.astype(int)), rotation=45)
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.title('Balance Sheet Composition')
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def draw_waterfall(cf, bs, filename):
    plt.figure(figsize=(6, 3))
    if cf.empty or bs.empty:
        plt.text(0.5, 0.5, 'Insufficient Data', ha='center', va='center')
        plt.savefig(filename)
        plt.close()
        return

    latest_cf = cf.iloc[-1]
    
    # Calculate CFF proxy
    if len(bs) >= 2:
        cff_proxy = bs.iloc[-1]['total_debt'] - bs.iloc[-2]['total_debt']
    else:
        cff_proxy = 0
        
    cfo = latest_cf['cfo']
    cfi = -abs(latest_cf['capex']) if pd.notna(latest_cf['capex']) else 0
    net = cfo + cfi + cff_proxy
    
    cats = ['CFO', 'CFI (CapEx)', 'CFF (Debt)', 'Net Change']
    vals = [cfo, cfi, cff_proxy, net]
    
    colors_list = ['g' if v > 0 else 'r' for v in vals[:-1]] + ['b']
    
    plt.bar(cats, vals, color=colors_list)
    plt.axhline(0, color='black', linewidth=1)
    plt.title(f"Cash Flow Waterfall ({latest_cf['year']})")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def generate_tearsheet(ticker):
    data = get_data(ticker)
    company = data['company']
    
    # Skip if less than 3 years
    if len(data['pl']) < 3:
        with open("output/skipped_tearsheets.csv", "a") as f:
            f.write(f"{ticker},Insufficient data\n")
        return False
        
    pdf_path = os.path.join(TEARSHEETS_DIR, f"{ticker}_tearsheet.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    # --- Page 1 ---
    # Header
    header_data = [[
        Paragraph(f"<b>{company['name']}</b>", title_style),
        Paragraph(f"Ticker: {ticker} | Sector: {company['sector']}", subtitle_style)
    ]]
    header_table = Table(header_data, colWidths=[4*inch, 3*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.darkblue),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 15),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # KPIs
    r = data['ratios'].iloc[-1] if not data['ratios'].empty else None
    pl = data['pl'].iloc[-1] if not data['pl'].empty else None
    
    def safe_value(value, suffix=""):
        if pd.isna(value):
            return "N/A"
        return f"{value:.2f}{suffix}"


    kpis = [
        ["Revenue", safe_value(pl["revenue"] if pl is not None else None, " Rs.")],
        ["Net Profit", safe_value(pl["pat"] if pl is not None else None, " Rs.")],
        ["ROE", safe_value(r["roe"] if r is not None else None, "%")],
        ["ROCE", safe_value(r["roce"] if r is not None else None, "%")],
        ["D/E Ratio", safe_value(r["de"] if r is not None else None)],
        ["OPM", safe_value(r["opm"] if r is not None else None, "%")]
    ]
    
    kpi_data = [
        [kpis[0][0], kpis[1][0], kpis[2][0]],
        [kpis[0][1], kpis[1][1], kpis[2][1]],
        [kpis[3][0], kpis[4][0], kpis[5][0]],
        [kpis[3][1], kpis[4][1], kpis[5][1]]
    ]
    
    kpi_table = Table(kpi_data, colWidths=[2.5*inch]*3)
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,2), (-1,2), 'Helvetica-Bold'),
        ('FONTSIZE', (0,1), (-1,1), 14),
        ('FONTSIZE', (0,3), (-1,3), 14),
        ('TEXTCOLOR', (0,1), (-1,1), colors.darkblue),
        ('TEXTCOLOR', (0,3), (-1,3), colors.darkblue),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.lightgrey),
        ('BOX', (0,0), (-1,-1), 0.25, colors.lightgrey),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 20))
    
    # Charts Page 1
    rev_chart = os.path.join(CHARTS_DIR, f"{ticker}_rev.png")
    draw_rev_pat_chart(data['pl'], rev_chart)
    
    roe_chart = os.path.join(CHARTS_DIR, f"{ticker}_roe.png")
    draw_roe_roce_chart(data['ratios'], roe_chart)
    
    chart_table = Table([[Image(rev_chart, width=3.5*inch, height=2*inch), Image(roe_chart, width=3.5*inch, height=2*inch)]])
    elements.append(chart_table)
    elements.append(PageBreak())
    
    # --- Page 2 ---
    # Charts Page 2
    bs_chart = os.path.join(CHARTS_DIR, f"{ticker}_bs.png")
    draw_bs_composition(data['bs'], bs_chart)
    
    cf_chart = os.path.join(CHARTS_DIR, f"{ticker}_cf.png")
    draw_waterfall(data['cf'], data['bs'], cf_chart)
    
    chart_table2 = Table([[Image(bs_chart, width=3.5*inch, height=2*inch), Image(cf_chart, width=3.5*inch, height=2*inch)]])
    elements.append(chart_table2)
    elements.append(Spacer(1, 20))
    
    # Pros and Cons
    elements.append(Paragraph("Strengths (Pros)", section_style))
    for pro in data['pros'][:5]: # Limit to 5
        elements.append(Paragraph(f"• {pro}", pro_style))
        
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Risks (Cons)", section_style))
    for con in data['cons'][:5]:
        elements.append(Paragraph(f"• {con}", con_style))
        
    elements.append(Spacer(1, 20))
    
    # Capital Allocation
    elements.append(Paragraph("Capital Allocation Strategy", section_style))
    elements.append(Paragraph(f"<b>Pattern Detected:</b> {data['pattern']}", styles['Normal']))
    
    doc.build(elements)
    return True

if __name__ == "__main__":
    # Ensure skipped tearsheets file exists and is empty
    with open("output/skipped_tearsheets.csv", "w") as f:
        f.write("ticker,reason\n")
    # Test generation for a few tickers
    for t in ["TCS", "HDFCBANK", "RELIANCE"]:
        print(f"Generating {t}...")
        generate_tearsheet(t)
    print("Done testing.")
