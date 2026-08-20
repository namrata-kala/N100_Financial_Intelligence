from fastapi import APIRouter, Depends, HTTPException
import sqlite3
import pandas as pd
import numpy as np
from src.api.db import get_db

router = APIRouter(prefix="/peers", tags=["Peers"])

@router.get("/{group_id}")
def get_peer_group(group_id: int, db: sqlite3.Connection = Depends(get_db)):
    # Assuming group_id maps to peer_group in companies table
    query = """
        SELECT c.company_id, c.ticker, c.name, r.*
        FROM companies c
        JOIN ratios r ON c.company_id = r.company_id
        WHERE c.peer_group = ? AND r.year = 2024
    """
    df = pd.read_sql_query(query, db, params=[group_id])
    if df.empty:
        raise HTTPException(status_code=404, detail="Peer group not found or empty")
        
    metrics = ['roe', 'roce', 'pe', 'pb', 'ev_ebitda', 'de', 'opm', 'npm', 'revenue_cagr_5yr', 'pat_cagr_5yr']
    
    # Calculate percentiles within peer group
    for metric in metrics:
        if metric in df.columns:
            df[f"{metric}_percentile"] = df[metric].rank(pct=True) * 100
            
    # Convert to dict and handle NaNs
    df = df.replace({np.nan: None})
    return df.to_dict(orient="records")

@router.get("/compare/{ticker}")
def compare_peers(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    company = db.execute("SELECT company_id, peer_group FROM companies WHERE ticker = ?", (ticker,)).fetchone()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    cid = company["company_id"]
    group_id = company["peer_group"]
    
    query = """
        SELECT c.company_id, c.ticker, r.*
        FROM companies c
        JOIN ratios r ON c.company_id = r.company_id
        WHERE c.peer_group = ? AND r.year = 2024
    """
    df = pd.read_sql_query(query, db, params=[group_id])
    
    metrics = ['roe', 'roce', 'pe', 'pb', 'ev_ebitda', 'de', 'opm', 'npm']
    
    company_data = df[df['company_id'] == cid].iloc[0]
    group_avg = df[metrics].mean()
    
    # Simple benchmark (highest market cap or highest ROE, let's use highest ROE)
    benchmark = df.loc[df['roe'].idxmax()]
    
    return {
        "metrics": metrics,
        "company": {m: float(company_data[m]) if pd.notnull(company_data[m]) else None for m in metrics},
        "group_average": {m: float(group_avg[m]) if pd.notnull(group_avg[m]) else None for m in metrics},
        "benchmark": {m: float(benchmark[m]) if pd.notnull(benchmark[m]) else None for m in metrics},
        "benchmark_ticker": benchmark['ticker']
    }
