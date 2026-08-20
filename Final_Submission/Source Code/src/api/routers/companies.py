from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
import sqlite3
import os
from src.api.db import get_db

router = APIRouter(prefix="/companies", tags=["Companies"])

@router.get("/")
def get_companies(sector: str = None, market_cap_category: str = None, search: str = None, db: sqlite3.Connection = Depends(get_db)):
    query = "SELECT company_id, ticker, name, sector as broad_sector, sub_sector, about FROM companies WHERE 1=1"
    params = []
    
    if sector:
        query += " AND sector = ?"
        params.append(sector)
    if search:
        query += " AND (name LIKE ? OR ticker LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
        
    companies = [dict(row) for row in db.execute(query, params).fetchall()]
    return companies

@router.get("/{ticker}")
def get_company_profile(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    company = db.execute("SELECT * FROM companies WHERE ticker = ?", (ticker,)).fetchone()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    company = dict(company)
    cid = company["company_id"]
    
    # Latest KPIs
    latest_ratios = db.execute("SELECT * FROM ratios WHERE company_id = ? ORDER BY year DESC LIMIT 1", (cid,)).fetchone()
    if latest_ratios:
        company["latest_kpis"] = dict(latest_ratios)
        
    return company

@router.get("/{ticker}/pl")
def get_company_pl(ticker: str, from_year: int = None, to_year: int = None, db: sqlite3.Connection = Depends(get_db)):
    company = db.execute("SELECT company_id FROM companies WHERE ticker = ?", (ticker,)).fetchone()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    cid = company["company_id"]
    query = "SELECT * FROM pl WHERE company_id = ?"
    params = [cid]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
        
    query += " ORDER BY year"
    return [dict(row) for row in db.execute(query, params).fetchall()]

@router.get("/{ticker}/bs")
def get_company_bs(ticker: str, from_year: int = None, to_year: int = None, db: sqlite3.Connection = Depends(get_db)):
    company = db.execute("SELECT company_id FROM companies WHERE ticker = ?", (ticker,)).fetchone()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    query = "SELECT * FROM balance_sheet WHERE company_id = ?"
    params = [company["company_id"]]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
        
    query += " ORDER BY year"
    return [dict(row) for row in db.execute(query, params).fetchall()]

@router.get("/{ticker}/cashflow")
def get_company_cf(ticker: str, from_year: int = None, to_year: int = None, db: sqlite3.Connection = Depends(get_db)):
    company = db.execute("SELECT company_id FROM companies WHERE ticker = ?", (ticker,)).fetchone()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    query = "SELECT * FROM cash_flow WHERE company_id = ?"
    params = [company["company_id"]]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
        
    query += " ORDER BY year"
    return [dict(row) for row in db.execute(query, params).fetchall()]

@router.get("/{ticker}/ratios")
def get_company_ratios(ticker: str, year: int = None, db: sqlite3.Connection = Depends(get_db)):
    company = db.execute("SELECT company_id FROM companies WHERE ticker = ?", (ticker,)).fetchone()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    query = "SELECT * FROM ratios WHERE company_id = ?"
    params = [company["company_id"]]
    if year:
        query += " AND year = ?"
        params.append(year)
        
    query += " ORDER BY year"
    return [dict(row) for row in db.execute(query, params).fetchall()]

@router.get("/{ticker}/tearsheet")
def get_tearsheet(ticker: str):
    file_path = f"reports/tearsheets/{ticker}_tearsheet.pdf"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Tearsheet not found")
    return FileResponse(file_path, media_type="application/pdf", filename=f"{ticker}_tearsheet.pdf")
