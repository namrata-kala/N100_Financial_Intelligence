import sqlite3
from pathlib import Path

DB_PATH = Path("db/nifty100.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 60)
print("MANUAL DATA REVIEW")
print("=" * 60)

# Review 5 sample companies
cursor.execute("""
SELECT id, company_name
FROM companies
ORDER BY RANDOM()
LIMIT 5;
""")

companies = cursor.fetchall()

for company_id, company_name in companies:

    print(f"\n{company_name} ({company_id})")

    cursor.execute("""
    SELECT COUNT(*), MIN(year), MAX(year)
    FROM profitandloss
    WHERE company_id = ?
    """, (company_id,))

    count, min_year, max_year = cursor.fetchone()

    print(f"Profit & Loss Records : {count}")
    print(f"Year Range            : {min_year} → {max_year}")

print("\n" + "=" * 60)
print("Companies with fewer than 5 Profit & Loss records")
print("=" * 60)

cursor.execute("""
SELECT company_id, COUNT(*) AS total_years
FROM profitandloss
GROUP BY company_id
HAVING COUNT(*) < 5
ORDER BY total_years;
""")

rows = cursor.fetchall()

if not rows:
    print("None")
else:
    for company_id, total in rows:
        print(f"{company_id:<15} {total}")

conn.close()