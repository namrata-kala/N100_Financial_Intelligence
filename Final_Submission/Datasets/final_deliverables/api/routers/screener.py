from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from src.api.db import get_db

router = APIRouter(prefix="/screener", tags=["Screener"])

@router.get("/")
def screen_companies(
    min_roe: float = None,
    max_de: float = None,
    min_fcf: float = None,
    sector: str = None,
    min_rev_cagr_5yr: float = None,
    min_pat_cagr_5yr: float = None,
    max_pe: float = None,
    db: sqlite3.Connection = Depends(get_db)
):
    # Validate params
    if min_roe is not None and min_roe < -100:
        raise HTTPException(status_code=400, detail="Invalid min_roe")
        
    query = """
        SELECT c.company_id, c.ticker, c.name, c.sector,
               r.roe, r.de as debt_to_equity, r.pe, r.revenue_cagr_5yr, r.pat_cagr_5yr,
               cf.fcf
        FROM companies c
        JOIN ratios r ON c.company_id = r.company_id
        JOIN cash_flow cf ON c.company_id = cf.company_id
        WHERE r.year = 2024 AND cf.year = 2024
    """
    params = []
    
    if min_roe is not None:
        query += " AND r.roe >= ?"
        params.append(min_roe)
    if max_de is not None:
        query += " AND r.de <= ?"
        params.append(max_de)
    if min_fcf is not None:
        query += " AND cf.fcf >= ?"
        params.append(min_fcf)
    if sector is not None:
        query += " AND c.sector = ?"
        params.append(sector)
    if min_rev_cagr_5yr is not None:
        query += " AND r.revenue_cagr_5yr >= ?"
        params.append(min_rev_cagr_5yr)
    if min_pat_cagr_5yr is not None:
        query += " AND r.pat_cagr_5yr >= ?"
        params.append(min_pat_cagr_5yr)
    if max_pe is not None:
        query += " AND r.pe <= ? AND r.pe > 0"
        params.append(max_pe)
        
    query += " ORDER BY r.roe DESC"
    
    results = [dict(row) for row in db.execute(query, params).fetchall()]
    return results
