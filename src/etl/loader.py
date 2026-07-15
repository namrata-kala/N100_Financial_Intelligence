from src.etl.validator import (
    validate_primary_key,
    validate_composite_key,
    validate_foreign_key,
    save_report,
)

from pathlib import Path
import pandas as pd

from src.etl.normaliser import normalize_ticker, normalize_year


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


def load_excel(file_path: Path) -> pd.DataFrame:
    """
    Load a single Excel file using the correct header.
    """

    header = 1 if file_path.name in CORE_FILES else 0

    df = pd.read_excel(file_path, header=header)

    return df


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize common columns.
    """

    # Normalize company_id
    if "company_id" in df.columns and "year" in df.columns:
        before = len(df)

        df = df.drop_duplicates(
            subset=["company_id", "year"],
            keep="first"
        )

        removed = before - len(df)

        if removed > 0:
            print(f"Removed {removed} duplicate rows")
            
    # companies.xlsx uses "id" as company identifier
    elif "id" in df.columns and "company_name" in df.columns:
        df["id"] = df["id"].apply(normalize_ticker)

    # documents.xlsx uses "Year"
    if "Year" in df.columns:
        df.rename(columns={"Year": "year"}, inplace=True)

    if "year" in df.columns:
        df["year"] = df["year"].apply(normalize_year)

    return df


def load_all_data():
    """
    Load all datasets.
    """

    datasets = {}

    for file in sorted(RAW_DATA.glob("*.xlsx")):

        df = load_excel(file)
        df = normalize_dataframe(df)

        datasets[file.stem] = df

    return datasets


def print_summary(datasets):
    print("\nDATASET SUMMARY")
    print("-" * 70)

    for name, df in datasets.items():
        print(
            f"{name:<20} Rows: {len(df):<6} Columns: {len(df.columns)}"
        )

PROCESSED_DATA = Path("data/processed")


def save_processed_data(datasets):
    """
    Save all cleaned datasets as CSV files.
    """

    PROCESSED_DATA.mkdir(exist_ok=True)

    for name, df in datasets.items():

        output_file = PROCESSED_DATA / f"{name}.csv"

        df.to_csv(output_file, index=False)

        print(f"Saved {output_file}")

def main():

    datasets = load_all_data()

    company_ids = set(datasets["companies"]["id"])

    print("\nNumber of companies:", len(company_ids))

    print("\nLast 15 company IDs:")
    print(sorted(company_ids)[-15:])
    print_summary(datasets)

    save_processed_data(datasets)

    print("\nRunning DQ-01 Validation...")
    print("-" * 50)

    for name, df in datasets.items():

        # DQ-01: Primary Key
        if "id" in df.columns:
            validate_primary_key(df, "id", name)

        # DQ-02: Composite Key
        if {"company_id", "year"}.issubset(df.columns):
            validate_composite_key(
                df,
                ["company_id", "year"],
                name,
            )
        
         # DQ-03
        validate_foreign_key(
            df,
            company_ids,
            name,
        )

    save_report()

    print(sorted(set(datasets["balancesheet"]["company_id"]) - company_ids))


    print(
        datasets["companies"][
            datasets["companies"]["company_name"]
            .str.contains(
                "Wipro|Ultra|Union|Ved|Zomato|Zydus",
                case=False,
                na=False
            )
        ][["id", "company_name"]]
    )

if __name__ == "__main__":
    main()