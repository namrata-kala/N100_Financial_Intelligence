from pathlib import Path
import pandas as pd

RAW_DATA = Path("data/raw")

CORE_FILES = {
    "companies.xlsx",
    "profitandloss.xlsx",
    "balancesheet.xlsx",
    "cashflow.xlsx",
    "analysis.xlsx",
    "documents.xlsx",
    "prosandcons.xlsx",
}


def inspect_excel(file_path):
    header = 1 if file_path.name in CORE_FILES else 0

    print("=" * 80)
    print(f"File: {file_path.name}")
    print(f"Header Row: {header}")

    try:
        df = pd.read_excel(file_path, header=header)

        print(f"Rows    : {df.shape[0]}")
        print(f"Columns : {df.shape[1]}")

        print("\nColumn Names")
        print(df.columns.tolist())

        print("\nFirst 5 Rows")
        print(df.head())

    except Exception as e:
        print(f"Error: {e}")


def main():
    files = sorted(RAW_DATA.glob("*.xlsx"))

    for file in files:
        inspect_excel(file)


if __name__ == "__main__":
    main()