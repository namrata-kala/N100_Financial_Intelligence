from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from src.api.db import get_db

router = APIRouter(prefix="/market-cap", tags=["Valuation"])

@router.get("/{ticker}")
def get_valuation(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    company = db.execute("SELECT company_id FROM companies WHERE ticker = ?", (ticker,)).fetchone()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    query = """
        SELECT year, market_cap, pe, pb, ev_ebitda, dividend_yield 
        FROM valuation 
        WHERE company_id = ? AND year >= 2019 AND year <= 2024
        ORDER BY year
    """
    results = [dict(row) for row in db.execute(query, (company["company_id"],)).fetchall()]
    return results
