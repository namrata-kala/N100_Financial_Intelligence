from fastapi import APIRouter, Depends, HTTPException
import sqlite3
import requests
from src.api.db import get_db

router = APIRouter(prefix="/companies", tags=["Documents"])

@router.get("/{ticker}/documents")
def get_documents(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    company = db.execute("SELECT company_id FROM companies WHERE ticker = ?", (ticker,)).fetchone()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    query = """
        SELECT year, annual_report_url 
        FROM documents 
        WHERE company_id = ?
        ORDER BY year DESC
    """
    results = [dict(row) for row in db.execute(query, (company["company_id"],)).fetchall()]
    
    # Add validation flag (using a HEAD request for speed, but catching exceptions)
    for res in results:
        url = res["annual_report_url"]
        is_valid = False
        if url:
            try:
                # Fast timeout so API doesn't hang
                resp = requests.head(url, timeout=2.0)
                is_valid = resp.status_code < 400
            except:
                is_valid = False
        res["is_url_valid"] = is_valid
        
    return results
