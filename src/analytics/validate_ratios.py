import sqlite3
import os

DB_PATH = "db/nifty100.db"
OUTPUT_DIR = "output"
LOG_FILE = os.path.join(OUTPUT_DIR, "ratio_edge_cases.log")

os.makedirs(OUTPUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

query = """
SELECT
    c.id,
    c.company_name,
    c.roe_percentage AS source_roe,
    c.roce_percentage AS source_roce,
    fr.return_on_equity_pct AS computed_roe,
    fr.year
FROM companies c
LEFT JOIN financial_ratios fr
    ON c.id = fr.company_id
WHERE fr.year = (
    SELECT MAX(fr2.year)
    FROM financial_ratios fr2
    WHERE fr2.company_id = c.id
      AND fr2.year <> 'TTM'
);
"""

rows = cursor.execute(query).fetchall()

THRESHOLD = 5.0

issues = []

for row in rows:
    company_id, company_name, source_roe, source_roce, computed_roe, year = row
    if source_roe is not None and computed_roe is not None:
        diff = abs(source_roe - computed_roe)

        if diff > THRESHOLD:
            issues.append(
                f"[ROE MISMATCH] {company_id} ({company_name}) | "
                f"Source={source_roe:.2f}% | "
                f"Computed={computed_roe:.2f}% | "
                f"Difference={diff:.2f}%"
            )

    elif source_roe is not None and computed_roe is None:
        issues.append(
            f"[ROE NULL] {company_id} ({company_name}) | "
            f"Year={year} | "
            f"Source={source_roe:.2f}% | Computed=NULL"
        )

with open(LOG_FILE, "w") as f:
    if issues:
        f.write("\n".join(issues))
    else:
        f.write("No significant ROE anomalies found.\n")

print(f"Validation complete.")
print(f"Issues found: {len(issues)}")
print(f"Log saved to: {LOG_FILE}")

conn.close()