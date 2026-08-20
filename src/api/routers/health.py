from fastapi import APIRouter, Depends
import time
import sqlite3
from src.api.db import get_db

router = APIRouter(tags=["Health"])

START_TIME = time.time()

@router.get("/health")
def health_check(db: sqlite3.Connection = Depends(get_db)):
    tables = [
        "companies", "peer_groups", "ratios", "pl", "balance_sheet", 
        "cash_flow", "valuation", "documents"
    ]
    counts = {}
    for t in tables:
        try:
            count = db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            counts[t] = count
        except Exception:
            counts[t] = 0
            
    return {
        "status": "ok",
        "uptime_seconds": int(time.time() - START_TIME),
        "version": "1.0.0",
        "db_row_counts": counts
    }
