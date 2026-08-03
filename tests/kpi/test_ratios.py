import unittest

from src.analytics.ratios import (
    debt_to_equity,
    high_leverage_flag,
    interest_coverage,
    icr_label,
    icr_warning,
    net_debt,
    asset_turnover,
)


class TestRatios(unittest.TestCase):

    # Debt to Equity
    def test_normal_debt_to_equity(self):
        self.assertEqual(debt_to_equity(100, 200, 300), 0.2)

    def test_zero_borrowings(self):
        self.assertEqual(debt_to_equity(0, 200, 300), 0)

    def test_negative_equity(self):
        self.assertIsNone(debt_to_equity(100, -50, -100))

    # High Leverage Flag
    def test_high_leverage_true(self):
        self.assertTrue(high_leverage_flag(6.0, "Technology"))

    def test_high_leverage_false_financials(self):
        self.assertFalse(high_leverage_flag(6.0, "Financials"))

    # Interest Coverage
    def test_interest_coverage(self):
        self.assertEqual(interest_coverage(100, 20, 10), 12.0)

    def test_interest_zero(self):
        self.assertIsNone(interest_coverage(100, 20, 0))

    # ICR Label
    def test_icr_label(self):
        self.assertEqual(icr_label(None), "Debt Free")

    # ICR Warning
    def test_icr_warning(self):
        self.assertTrue(icr_warning(1.2))

    # Net Debt
    def test_net_debt(self):
        self.assertEqual(net_debt(500, 200), 300)

    # Asset Turnover
    def test_asset_turnover(self):
        self.assertEqual(asset_turnover(1000, 500), 2.0)

    def test_asset_turnover_zero_assets(self):
        self.assertIsNone(asset_turnover(1000, 0))


if __name__ == "__main__":
    unittest.main()