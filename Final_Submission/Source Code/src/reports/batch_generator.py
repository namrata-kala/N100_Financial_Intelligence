import sqlite3
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
)

# -----------------------------
# Project Paths
# -----------------------------
BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "data" / "nifty100.db"

REPORTS_DIR = BASE_DIR / "reports"
SECTOR_DIR = REPORTS_DIR / "sector"
PORTFOLIO_DIR = REPORTS_DIR / "portfolio"

SECTOR_DIR.mkdir(parents=True, exist_ok=True)
PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)

# Import tearsheet generator
try:
    from src.reports.tearsheet import generate_tearsheet
except ModuleNotFoundError:
    from tearsheet import generate_tearsheet

# -----------------------------
# Styles
# -----------------------------
styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "Title",
    parent=styles["Heading1"],
    fontSize=20,
    spaceAfter=20,
)

h2_style = ParagraphStyle(
    "Heading2",
    parent=styles["Heading2"],
    fontSize=16,
    spaceAfter=10,
)

normal_style = ParagraphStyle(
    "Normal",
    parent=styles["Normal"],
    fontSize=10,
)

def generate_sector_reports():
    conn = sqlite3.connect(DB_PATH)
    companies = pd.read_sql("SELECT company_id, ticker, name, sector FROM companies", conn)
    ratios = pd.read_sql("SELECT * FROM ratios WHERE year=2024", conn)
    pl = pd.read_sql("SELECT * FROM pl WHERE year=2024", conn)
    conn.close()
    
    df = pd.merge(companies, ratios, on="company_id", how="left")
    df = pd.merge(df, pl, on="company_id", how="left")
    
    sectors = df['sector'].unique()
    
    for sector in sectors:
        sec_df = df[df['sector'] == sector].copy()
        if sec_df.empty: continue
        
        # Sector name to safe filename
        safe_sec = sector.replace(" ", "_").replace("/", "_")
        pdf_path = str(Path(SECTOR_DIR) / f"{safe_sec}_report.pdf")
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []
        
        # Page 1: Sector Summary
        elements.append(Paragraph(f"Sector Report: {sector}", title_style))
        elements.append(Paragraph(f"Total Companies: {len(sec_df)}", normal_style))
        elements.append(Spacer(1, 20))
        
        elements.append(Paragraph("Sector Medians (FY 24)", h2_style))
        numeric_cols = ["roe", "roce", "pe", "revenue", "pat", "de"]

        for col in numeric_cols:
            sec_df[col] = pd.to_numeric(sec_df[col], errors="coerce")

        medians = sec_df[numeric_cols].median(numeric_only=True).round(2)
        m_data = [
            ["Metric", "Median Value"],
            ["ROE %", f"{medians['roe']}"],
            ["ROCE %", f"{medians['roce']}"],
            ["P/E Ratio", f"{medians['pe']}"],
            ["Revenue (₹Cr)", f"{medians['revenue']}"],
            ["Net Profit (₹Cr)", f"{medians['pat']}"],
            ["D/E Ratio", f"{medians['de']}"]
        ]
        m_table = Table(m_data, colWidths=[2.5*inch, 2.5*inch])
        m_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        elements.append(m_table)
        elements.append(PageBreak())
        
        # Page 2: Company List
        elements.append(Paragraph(f"{sector} - Company Constituents", title_style))
        
        header = ["Ticker", "Rev", "PAT", "ROE", "ROCE", "P/E", "D/E", "OPM"]
        c_data = [header]
        for _, row in sec_df.iterrows():
            c_data.append([
                str(row['ticker'])[:10],
                f"{pd.to_numeric(row['revenue'], errors='coerce') if pd.notna(row['revenue']) else 0:.1f}",
                f"{pd.to_numeric(row['pat'], errors='coerce') if pd.notna(row['pat']) else 0:.1f}",
                f"{pd.to_numeric(row['roe'], errors='coerce') if pd.notna(row['roe']) else 0:.1f}",
                f"{pd.to_numeric(row['roce'], errors='coerce') if pd.notna(row['roce']) else 0:.1f}",
                f"{pd.to_numeric(row['pe'], errors='coerce') if pd.notna(row['pe']) else 0:.1f}",
                f"{pd.to_numeric(row['de'], errors='coerce') if pd.notna(row['de']) else 0:.2f}",
                f"{pd.to_numeric(row['opm'], errors='coerce') if pd.notna(row['opm']) else 0:.1f}",
            ])
            
        # Add word wrap by wrapping elements in Paragraphs
        wrapped_data = []
        for r in c_data:
            wrapped_data.append([Paragraph(cell, normal_style) for cell in r])
            
        c_table = Table(wrapped_data, colWidths=[1*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.7*inch, 0.7*inch, 0.7*inch])
        c_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(c_table)
        
        # Allow the company table to split across pages
        c_table.splitByRow = 1

        elements.append(c_table)

        doc.build(elements)

        print(f"Generated Sector Report: {sector}")

def generate_portfolio_summary():
    conn = sqlite3.connect(DB_PATH)
    companies = pd.read_sql("SELECT company_id, ticker, name, sector FROM companies ORDER BY ticker", conn)
    ratios_24 = pd.read_sql("SELECT * FROM ratios WHERE year=2024", conn)
    ratios_23 = pd.read_sql("SELECT * FROM ratios WHERE year=2023", conn)
    conn.close()
    
    df = pd.merge(companies, ratios_24, on="company_id", how="left")
    df = pd.merge(df, ratios_23, on="company_id", suffixes=("_24", "_23"), how="left")
    
    pdf_path = str(Path(PORTFOLIO_DIR) / "portfolio_summary.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    elements.append(Paragraph("Nifty 100 Portfolio Summary", title_style))
    elements.append(Spacer(1, 20))
    
    for _, row in df.iterrows():
        elements.append(Paragraph(f"<b>{row['name']} ({row['ticker']})</b> - {row['sector']}", h2_style))
        
        # Determine trends
        def get_trend(curr, prev):
            if pd.isna(curr) or pd.isna(prev): return "-"
            if curr > prev * 1.02: return "↑"
            if curr < prev * 0.98: return "↓"
            return "→"
            
        t_roe = get_trend(row['roe_24'], row['roe_23'])
        t_roce = get_trend(row['roce_24'], row['roce_23'])
        t_pe = get_trend(row['pe_24'], row['pe_23'])
        t_opm = get_trend(row['opm_24'], row['opm_23'])
        t_de = get_trend(row['de_24'], row['de_23']) # Lower is better, but just show direction
        t_cagr = get_trend(row['revenue_cagr_5yr_24'], row['revenue_cagr_5yr_23'])
        
        kpi_data = [
            ["Metric", "Value (FY24)", "Trend (vs FY23)"],
            ["ROE", f"{row['roe_24']}%", t_roe],
            ["ROCE", f"{row['roce_24']}%", t_roce],
            ["P/E", f"{row['pe_24']}", t_pe],
            ["OPM", f"{row['opm_24']}%", t_opm],
            ["D/E", f"{row['de_24']}", t_de],
            ["Rev CAGR", f"{row['revenue_cagr_5yr_24']}%", t_cagr]
        ]
        
        k_table = Table(kpi_data, colWidths=[2*inch, 2*inch, 2*inch])
        k_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ]))
        
        elements.append(k_table)
        elements.append(PageBreak())
        
    doc.build(elements)
    print("Generated Portfolio Summary.")

def run_all():
    print("1. Generating 92 Tearsheets...")
    conn = sqlite3.connect(DB_PATH)
    tickers = pd.read_sql("SELECT ticker FROM companies", conn)['ticker'].tolist()
    conn.close()
    
    for t in tickers:
        generate_tearsheet(t)
        
    print("2. Generating Sector Reports...")
    generate_sector_reports()
    
    print("3. Generating Portfolio Summary...")
    generate_portfolio_summary()

if __name__ == "__main__":
    run_all()
