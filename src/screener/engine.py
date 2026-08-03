import sqlite3
from pathlib import Path

import pandas as pd
import yaml


BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "db" / "nifty100.db"
CONFIG_PATH = BASE_DIR / "config" / "screener_config.yaml"


class ScreenerEngine:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)

        with open(CONFIG_PATH, "r") as f:
            self.config = yaml.safe_load(f)

    def load_data(self):
        query = """
        SELECT
            fr.*,
            s.broad_sector,
            a.compounded_sales_growth,
            a.compounded_profit_growth,
            a.stock_price_cagr,
            a.roe AS analysis_roe
        FROM financial_ratios fr
        LEFT JOIN sectors s
            ON fr.company_id = s.company_id
        LEFT JOIN analysis a
            ON fr.company_id = a.company_id
        """

        df = pd.read_sql(query, self.conn)

        # Remove TTM rows
        df = df[df["year"] != "TTM"]

        # Keep latest annual record for each company
        df = (
            df.sort_values("year")
            .groupby("company_id", as_index=False)
            .tail(1)
            .reset_index(drop=True)
        )

        if "composite_quality_score" not in df.columns:
            df["composite_quality_score"] = None

        return df
    
    def calculate_composite_score(self, df):
        """
        Calculate a weighted composite quality score (0–100)
        """

        score_df = df.copy()

        metrics = {
            "return_on_equity_pct": True,      # Higher is better
            "revenue_cagr_5yr": True,
            "pat_cagr_5yr": True,
            "free_cash_flow_cr": True,
            "debt_to_equity": False            # Lower is better
        }

        weights = {
            "return_on_equity_pct": 0.25,
            "revenue_cagr_5yr": 0.20,
            "pat_cagr_5yr": 0.20,
            "free_cash_flow_cr": 0.15,
            "debt_to_equity": 0.20
        }

        score_df["composite_quality_score"] = 0.0

        for column, higher_is_better in metrics.items():

            values = pd.to_numeric(score_df[column], errors="coerce")

            lower = values.quantile(0.05)
            upper = values.quantile(0.95)

            values = values.clip(lower, upper)

            minimum = values.min()
            maximum = values.max()

            if pd.isna(minimum) or pd.isna(maximum) or minimum == maximum:
                normalized = pd.Series(50, index=score_df.index)
            else:
                normalized = (values - minimum) / (maximum - minimum) * 100

                if not higher_is_better:
                    normalized = 100 - normalized

            score_df["composite_quality_score"] += (
                normalized.fillna(0) * weights[column]
            )

        return score_df

    def get_top_companies(self, n=10):
        """
        Return the top N companies ranked by composite quality score.
        """
        df = self.load_data()
        df = self.calculate_composite_score(df)

        return (
            df.sort_values(
                by="composite_quality_score",
                ascending=False
            )
            .head(n)
            .reset_index(drop=True)
        )

    def compare_company(self, company_id):
        """
        Compare a company against others in the same sector.
        """

        df = self.load_data()
        df = self.calculate_composite_score(df)

        company_id = company_id.upper()

        company = df[df["company_id"].str.upper() == company_id]

        if company.empty:
            raise ValueError(f"Company '{company_id}' not found.")

        sector = company.iloc[0]["broad_sector"]

        peers = (
            df[df["broad_sector"] == sector]
            .sort_values(
                by="composite_quality_score",
                ascending=False
            )
            .reset_index(drop=True)
        )

        peers["sector_rank"] = peers.index + 1

        columns = [
            "company_id",
            "broad_sector",
            "composite_quality_score",
            "return_on_equity_pct",
            "revenue_cagr_5yr",
            "pat_cagr_5yr",
            "debt_to_equity",
            "free_cash_flow_cr",
        ]

        selected = peers[
            peers["company_id"].str.upper() == company_id
        ]

        print(
            f"\n{company_id} ranks "
            f"#{selected.iloc[0]['sector_rank']} "
            f"in {sector}"
        )

        columns = [
            "sector_rank",
            "company_id",
            "broad_sector",
            "composite_quality_score",
            "return_on_equity_pct",
            "revenue_cagr_5yr",
            "pat_cagr_5yr",
            "debt_to_equity",
            "free_cash_flow_cr",
        ]

        display_df = peers[columns].fillna("N/A")

        return display_df

    def apply_filters(self, preset_name):
        df = self.load_data().copy()

        if preset_name not in self.config:
            raise ValueError(f"Unknown preset: {preset_name}")

        filters = self.config[preset_name]

        # ROE minimum
        if "roe_min" in filters:
            df = df[df["return_on_equity_pct"] >= filters["roe_min"]]

        # Debt-to-Equity maximum
        if "debt_to_equity_max" in filters:
            limit = filters["debt_to_equity_max"]

            financial_mask = df["broad_sector"].fillna("").str.contains(
                "Financial", case=False
            )

            df = df[
                financial_mask |
                (df["debt_to_equity"] <= limit)
            ]

        # Free Cash Flow minimum
        if "free_cash_flow_min" in filters:
            df = df[
                df["free_cash_flow_cr"] >= filters["free_cash_flow_min"]
            ]

        # Revenue CAGR minimum
        if "revenue_cagr_5yr_min" in filters:
            df = df[
                df["revenue_cagr_5yr"] >= filters["revenue_cagr_5yr_min"]
            ]

        # PAT CAGR minimum
        if "pat_cagr_5yr_min" in filters:
            df = df[
                df["pat_cagr_5yr"] >= filters["pat_cagr_5yr_min"]
            ]

        # Dividend payout maximum
        if "dividend_payout_ratio_pct_max" in filters:
            df = df[
                df["dividend_payout_ratio_pct"]
                <= filters["dividend_payout_ratio_pct_max"]
            ]

        if "compounded_sales_growth_min" in filters:
            df = df[
                pd.to_numeric(df["compounded_sales_growth"], errors="coerce")
                >= filters["compounded_sales_growth_min"]
            ]

        if "compounded_profit_growth_min" in filters:
            df = df[
                pd.to_numeric(df["compounded_profit_growth"], errors="coerce")
                >= filters["compounded_profit_growth_min"]
            ]

        if "stock_price_cagr_min" in filters:
            df = df[
                pd.to_numeric(df["stock_price_cagr"], errors="coerce")
                >= filters["stock_price_cagr_min"]
            ]

        df = self.calculate_composite_score(df)

        return df.sort_values(
            by="composite_quality_score",
            ascending=False
        ).reset_index(drop=True)