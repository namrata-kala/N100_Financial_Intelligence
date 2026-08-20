from fastapi import APIRouter, Depends, HTTPException
import sqlite3
import pandas as pd
from src.api.db import get_db

router = APIRouter(prefix="/sectors", tags=["Sectors"])

@router.get("/")
def get_sectors(db: sqlite3.Connection = Depends(get_db)):
    query = """
        SELECT c.sector, count(c.company_id) as company_count,
               r.roe, r.pe, r.de
        FROM companies c
        JOIN ratios r ON c.company_id = r.company_id
        WHERE r.year = 2024
    """
    df = pd.read_sql_query(query.replace("count(c.company_id) as company_count,", ""), db, params=[])
    counts = pd.read_sql_query("SELECT sector, count(company_id) as company_count FROM companies GROUP BY sector", db)
    
    medians = df.groupby('sector')[['roe', 'pe', 'de']].median().reset_index()
    result_df = pd.merge(counts, medians, on='sector')
    
    result = []
    for _, row in result_df.iterrows():
        result.append({
            "sector": row["sector"],
            "company_count": int(row["company_count"]),
            "median_roe": float(row["roe"]) if pd.notnull(row["roe"]) else None,
            "median_pe": float(row["pe"]) if pd.notnull(row["pe"]) else None,
            "median_de": float(row["de"]) if pd.notnull(row["de"]) else None,
        })
    return result

@router.get("/{sector}/companies")
def get_sector_companies(sector: str, db: sqlite3.Connection = Depends(get_db)):
    query = """
        SELECT c.company_id, c.ticker, c.name, r.roe, r.pe, r.de, r.revenue_cagr_5yr
        FROM companies c
        JOIN ratios r ON c.company_id = r.company_id
        WHERE c.sector = ? AND r.year = 2024
    """
    results = [dict(row) for row in db.execute(query, (sector,)).fetchall()]
    if not results:
        raise HTTPException(status_code=404, detail="Sector not found or no companies in sector")
    return results
