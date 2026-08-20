from fastapi import APIRouter
import pandas as pd
import os

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

@router.get("/stats")
def get_portfolio_stats():
    file_path = "output/portfolio_stats.csv"
    if not os.path.exists(file_path):
        return []
    
    df = pd.read_csv(file_path)
    return df.to_dict(orient="records")
