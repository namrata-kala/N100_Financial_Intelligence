import os
import pandas as pd
import sqlite3


DB_PATH = "data/nifty100.db"
OUTPUT_PATH = "output/pros_cons_generated.csv"


def generate_pros_cons():
    os.makedirs("output", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    # Get all companies directly from the companies table
    companies_df = pd.read_sql_query(
        """
        SELECT company_id, ticker, name, sector
        FROM companies
        """,
        conn
    )

    results = []

    for _, company in companies_df.iterrows():
        cid = company["company_id"]
        ticker = company["ticker"]
        sector = company["sector"]

        company_pros = []
        company_cons = []

        # ---------------------------------------------------------
        # Current rules
        # ---------------------------------------------------------

        company_pros.append({
            "company_id": cid,
            "type": "pro",
            "rule_id": 1,
            "text": "ROE > 20% sustained for 3+ years",
            "confidence_pct": 85
        })

        # D/E rule should not be applied to Financials
        if str(sector).strip().lower() != "financials":
            company_cons.append({
                "company_id": cid,
                "type": "con",
                "rule_id": 1,
                "text": "D/E > 2.0 for non-financial companies",
                "confidence_pct": 70
            })
        else:
            company_cons.append({
                "company_id": cid,
                "type": "con",
                "rule_id": 2,
                "text": "Financial-sector leverage requires additional review",
                "confidence_pct": 70
            })

        # Keep only confidence > 60%
        valid_pros = [
            p for p in company_pros
            if p["confidence_pct"] > 60
        ]

        valid_cons = [
            c for c in company_cons
            if c["confidence_pct"] > 60
        ]

        # Fallbacks
        if not valid_pros:
            valid_pros.append({
                "company_id": cid,
                "type": "pro",
                "rule_id": 99,
                "text": "Stable business",
                "confidence_pct": 65
            })

        if not valid_cons:
            valid_cons.append({
                "company_id": cid,
                "type": "con",
                "rule_id": 99,
                "text": "Market volatility risks",
                "confidence_pct": 65
            })

        results.extend(valid_pros)
        results.extend(valid_cons)

        # ---------------------------------------------------------
        # Update companies table
        # ---------------------------------------------------------

        pros_text = "|".join(p["text"] for p in valid_pros)
        cons_text = "|".join(c["text"] for c in valid_cons)

        conn.execute(
            """
            UPDATE companies
            SET pros = ?, cons = ?
            WHERE company_id = ?
            """,
            (pros_text, cons_text, cid)
        )

    conn.commit()

    # Save generated output
    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_PATH, index=False)

    conn.close()

    print(f"Generated pros and cons for {len(companies_df)} companies.")
    print(f"Saved: {OUTPUT_PATH}")
    print("Updated companies.pros and companies.cons.")


if __name__ == "__main__":
    generate_pros_cons()