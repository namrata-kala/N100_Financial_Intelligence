from pathlib import Path
import sqlite3
import pandas as pd

DB_PATH = Path("db/nifty100.db")
PROCESSED_DATA = Path("data/processed")

TABLES = [
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "analysis",
    "documents",
    "prosandcons",
    "sectors",
    "stock_prices",
    "financial_ratios",
]

def load_database():

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")

    # Clear existing data
    for table in reversed(TABLES):
        conn.execute(f"DELETE FROM {table}")
    conn.commit()

    company_ids = None
    audit = []

    for table in TABLES:

        file = PROCESSED_DATA / f"{table}.csv"
        df = pd.read_csv(file)
        source_rows = len(df)
        removed = 0

        # Save valid company IDs after loading companies.csv
        if table == "companies":
            company_ids = set(df["id"])

        # Filter invalid foreign keys
        elif "company_id" in df.columns:
            original_rows = len(df)

            df = df[df["company_id"].isin(company_ids)]

            removed = original_rows - len(df)

            if removed > 0:
                print(f"{table}: Removed {removed} invalid rows")

        try:
            df.to_sql(
                table,
                conn,
                if_exists="append",
                index=False,
            )

            print(f"✓ {table:<20} {len(df)} rows inserted")

            audit.append({
                "table": table,
                "source_rows": source_rows,
                "inserted_rows": len(df),
                "rejected_rows": removed,
                "status": "SUCCESS"
            })

        except Exception as e:
            print(f"\n❌ Failed while loading table: {table}")
            print(e)

            audit.append({
                "table": table,
                "source_rows": source_rows,
                "inserted_rows": 0,
                "rejected_rows": source_rows,
                "status": "FAILED"
            })
            
            break

    conn.commit()

    audit_df = pd.DataFrame(audit)
    audit_df.to_csv("output/load_audit.csv", index=False)

    print("\nLoad audit saved to output/load_audit.csv")

    conn.close()

if __name__ == "__main__":
    load_database()