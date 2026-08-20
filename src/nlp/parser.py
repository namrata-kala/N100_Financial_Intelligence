import re
import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data/raw/analysis.xlsx")
OUTPUT_DIR = Path("output")

OUTPUT_DIR.mkdir(exist_ok=True)

# -------------------------------
# Load Excel
# -------------------------------

df = pd.read_excel(INPUT_FILE, header=None)

# Remove title row
df = df.iloc[1:].reset_index(drop=True)

# Promote first row to header
df.columns = df.iloc[0]

# Remove duplicated header row
df = df.iloc[1:].reset_index(drop=True)

# -------------------------------
# Fields to parse
# -------------------------------

FIELDS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe"
]

year_pattern = re.compile(r"(\d+)\s*Years?:?\s*([\d.-]+)%")
ttm_pattern = re.compile(r"TTM:?\s*([\d.-]+)%", re.IGNORECASE)
last_year_pattern = re.compile(r"Last\s*Year:?\s*([\d.-]+)%", re.IGNORECASE)

parsed_rows = []
failed_rows = []

# -------------------------------
# Parse
# -------------------------------

for _, row in df.iterrows():

    company = row["company_id"]

    for field in FIELDS:

        value = str(row[field]).strip()

        match = year_pattern.search(value)

        if match:

            period = int(match.group(1))
            value_pct = float(match.group(2))

        elif ttm_pattern.search(value):

            period = 0          # 0 = TTM
            value_pct = float(ttm_pattern.search(value).group(1))

        elif last_year_pattern.search(value):

            period = 1          # 1 = Last Year
            value_pct = float(last_year_pattern.search(value).group(1))

        else:

            failed_rows.append({
                "company_id": company,
                "metric_type": field,
                "raw_text": value
            })
            continue

        parsed_rows.append({
            "company_id": company,
            "metric_type": field,
            "period_years": period,
            "value_pct": value_pct
        })

# -------------------------------
# Save outputs
# -------------------------------

parsed_df = pd.DataFrame(parsed_rows)
failed_df = pd.DataFrame(failed_rows)

parsed_df.to_csv(
    OUTPUT_DIR / "analysis_parsed.csv",
    index=False
)

failed_df.to_csv(
    OUTPUT_DIR / "parse_failures.csv",
    index=False
)

print("=" * 50)
print("Parsing Complete")
print("=" * 50)
print(f"Parsed rows : {len(parsed_df)}")
print(f"Failed rows : {len(failed_df)}")
print(f"Saved : {OUTPUT_DIR/'analysis_parsed.csv'}")
print(f"Saved : {OUTPUT_DIR/'parse_failures.csv'}")