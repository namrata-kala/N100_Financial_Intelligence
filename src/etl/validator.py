from pathlib import Path
import pandas as pd

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Global list to hold our DQ failures
validation_results = []

def add_failure(rule: str, severity: str, dataset: str, row: int, message: str):
    """
    Store validation failures.
    """
    validation_results.append({
        "rule": rule,
        "severity": severity,
        "dataset": dataset,
        "row": row,
        "message": message
    })

def save_report():
    """
    Export the collected failures to the required CSV deliverable.
    """
    df = pd.DataFrame(validation_results)
    
    # If there are no failures, create an empty DataFrame with the correct headers
    if df.empty:
        df = pd.DataFrame(columns=["rule", "severity", "dataset", "row", "message"])
        
    output_file = OUTPUT_DIR / "validation_failures.csv"
    df.to_csv(output_file, index=False)
    print(f"\nValidation report saved to {output_file}")

def validate_primary_key(df: pd.DataFrame, column: str, dataset: str):
    """
    DQ-01: Validate that the primary key column has unique values.
    """
    # keep=False ensures ALL instances of the duplicate are flagged, not just the second one
    duplicates = df[df.duplicated(subset=[column], keep=False)]

    if duplicates.empty:
        print(f"[{dataset}] DQ-01 Primary Key: PASS")
        return

    print(f"[{dataset}] DQ-01 Primary Key: FAIL ({len(duplicates)} duplicate rows found)")

    for index, row in duplicates.iterrows():
        add_failure(
            rule="DQ-01",
            severity="CRITICAL",
            dataset=dataset,
            row=index,
            message=f"Duplicate primary key '{column}': {row[column]}"
        )


def validate_composite_key(df: pd.DataFrame, columns: list, dataset: str):
    """
    DQ-02: Validate that a combination of columns (e.g., company_id, year) is unique.
    """
    duplicates = df[df.duplicated(subset=columns, keep=False)]

    if duplicates.empty:
        print(f"[{dataset}] DQ-02 Composite Key: PASS")
        return

    print(f"[{dataset}] DQ-02 Composite Key: FAIL ({len(duplicates)} duplicate rows found)")
    print(f"\nSample of duplicate rows for {dataset}:")
    print(duplicates[columns].head(5)) # Only print a small sample for terminal readability

    for index, row in duplicates.iterrows():
        # Create a readable string of the composite key values
        key = " | ".join(str(row[col]) for col in columns)
        
        add_failure(
            rule="DQ-02",
            severity="CRITICAL",
            dataset=dataset,
            row=index, # This will be the pandas index. You might want index+2 if matching Excel row numbers.
            message=f"Duplicate composite key for {columns}: {key}"
        )

def validate_foreign_key(df, parent_keys, dataset):
    """
    Validate that every company_id exists in companies table.
    """

    if "company_id" not in df.columns:
        return

    invalid_rows = df[~df["company_id"].isin(parent_keys)]

    if invalid_rows.empty:
        print(f"[{dataset}] DQ-03 Foreign Key: PASS")
        return

    print(f"[{dataset}] DQ-03 Foreign Key: FAIL")
    print("\nInvalid company IDs:")
    print(invalid_rows["company_id"].unique())

    for index, row in invalid_rows.iterrows():
        add_failure(
            rule="DQ-03",
            severity="CRITICAL",
            dataset=dataset,
            row=index,
            message=f"Invalid company_id: {row['company_id']}"
        )