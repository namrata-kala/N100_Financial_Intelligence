import unittest

from src.analytics.cagr import calculate_cagr


class TestCAGR(unittest.TestCase):

    def test_normal(self):
        value, flag = calculate_cagr(100, 200, 5)
        self.assertEqual(flag, "OK")
        self.assertIsNotNone(value)

    def test_zero_base(self):
        value, flag = calculate_cagr(0, 200, 5)
        self.assertIsNone(value)
        self.assertEqual(flag, "ZERO_BASE")

    def test_turnaround(self):
        value, flag = calculate_cagr(-100, 200, 5)
        self.assertIsNone(value)
        self.assertEqual(flag, "TURNAROUND")

    def test_decline_to_loss(self):
        value, flag = calculate_cagr(100, -50, 5)
        self.assertIsNone(value)
        self.assertEqual(flag, "DECLINE_TO_LOSS")

    def test_both_negative(self):
        value, flag = calculate_cagr(-100, -50, 5)
        self.assertIsNone(value)
        self.assertEqual(flag, "BOTH_NEGATIVE")

    def test_insufficient(self):
        value, flag = calculate_cagr(100, 200, 0)
        self.assertIsNone(value)
        self.assertEqual(flag, "INSUFFICIENT")

if __name__ == "__main__":
    unittest.main()