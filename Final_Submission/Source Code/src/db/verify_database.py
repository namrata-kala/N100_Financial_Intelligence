import sqlite3
from pathlib import Path

DB_PATH = Path("db/nifty100.db")

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

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("\nDATABASE ROW COUNTS")
print("-" * 40)

for table in TABLES:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"{table:<20} {count}")

print("\nFOREIGN KEY CHECK")
print("-" * 40)

cursor.execute("PRAGMA foreign_key_check")

errors = cursor.fetchall()

if not errors:
    print("PASS")
else:
    print("FAIL")
    print(errors)

conn.close()