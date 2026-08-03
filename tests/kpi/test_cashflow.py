import unittest

from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality_score,
    capex_intensity,
    fcf_conversion_rate,
    capital_allocation_pattern,
)

class TestCashFlowKPIs(unittest.TestCase):

    def test_positive_fcf(self):
        self.assertEqual(
            free_cash_flow(500, -100),
            400
        )

    def test_negative_fcf(self):
        self.assertEqual(
            free_cash_flow(100, -300),
            -200
        )

    def test_zero_fcf(self):
        self.assertEqual(
            free_cash_flow(200, -200),
            0
        )

    def test_high_quality(self):
        ratio, label = cfo_quality_score(120, 100)

        self.assertEqual(ratio, 1.2)
        self.assertEqual(label, "High Quality")


    def test_moderate(self):
        ratio, label = cfo_quality_score(75, 100)

        self.assertEqual(ratio, 0.75)
        self.assertEqual(label, "Moderate")


    def test_accrual_risk(self):
        ratio, label = cfo_quality_score(20, 100)

        self.assertEqual(ratio, 0.2)
        self.assertEqual(label, "Accrual Risk")


    def test_zero_pat(self):
        ratio, label = cfo_quality_score(100, 0)

        self.assertIsNone(ratio)
        self.assertIsNone(label)

    def test_asset_light(self):
        intensity, category = capex_intensity(-20, 1000)

        self.assertEqual(intensity, 2.0)
        self.assertEqual(category, "Asset Light")


    def test_moderate_capex(self):
        intensity, category = capex_intensity(-50, 1000)

        self.assertEqual(intensity, 5.0)
        self.assertEqual(category, "Moderate")


    def test_capital_intensive(self):
        intensity, category = capex_intensity(-150, 1000)

        self.assertEqual(intensity, 15.0)
        self.assertEqual(category, "Capital Intensive")


    def test_zero_sales(self):
        intensity, category = capex_intensity(-50, 0)

        self.assertIsNone(intensity)
        self.assertIsNone(category)

    def test_fcf_conversion_positive(self):
        self.assertEqual(
            fcf_conversion_rate(200, 400),
            50.0
        )


    def test_fcf_conversion_negative(self):
        self.assertEqual(
            fcf_conversion_rate(-100, 200),
            -50.0
        )


    def test_fcf_conversion_zero_operating_profit(self):
        self.assertIsNone(
            fcf_conversion_rate(100, 0)
        )

    def test_reinvestor(self):
        self.assertEqual(
            capital_allocation_pattern(100, -50, -20),
            "Reinvestor"
        )


    def test_shareholder_returns(self):
        self.assertEqual(
            capital_allocation_pattern(
                100,
                -50,
                -20,
                "High Quality"
            ),
            "Shareholder Returns"
        )


    def test_liquidating_assets(self):
        self.assertEqual(
            capital_allocation_pattern(100, 50, -10),
            "Liquidating Assets"
        )


    def test_distress_signal(self):
        self.assertEqual(
            capital_allocation_pattern(-100, 50, 20),
            "Distress Signal"
        )


    def test_growth_funded_by_debt(self):
        self.assertEqual(
            capital_allocation_pattern(-100, -50, 20),
            "Growth Funded by Debt"
        )


    def test_cash_accumulator(self):
        self.assertEqual(
            capital_allocation_pattern(100, 50, 20),
            "Cash Accumulator"
        )


    def test_pre_revenue(self):
        self.assertEqual(
            capital_allocation_pattern(-100, -50, -20),
            "Pre-Revenue"
        )


    def test_mixed(self):
        self.assertEqual(
            capital_allocation_pattern(100, -50, 20),
            "Mixed"
        )

if __name__ == "__main__":
    unittest.main()