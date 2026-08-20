from src.analytics.ratios import debt_to_equity

print(debt_to_equity(100, 200, 300))
print(debt_to_equity(0, 200, 300))
print(debt_to_equity(100, -50, -100))