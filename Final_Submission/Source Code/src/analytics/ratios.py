def high_leverage_flag(de_ratio, sector):
    if de_ratio is None:
        return False

    return de_ratio > 5 and sector != "Financials"

def interest_coverage(
    operating_profit,
    other_income,
    interest
):
    if interest == 0:
        return None

    return (operating_profit + other_income) / interest

def icr_label(icr):
    if icr is None:
        return "Debt Free"

    return ""

def icr_warning(icr):
    if icr is None:
        return False

    return icr < 1.5

def net_debt(
    borrowings,
    investments
):
    return borrowings - investments

def asset_turnover(
    sales,
    total_assets
):
    if total_assets == 0:
        return None

    return sales / total_assets

def debt_to_equity(borrowings, equity_capital, reserves):
    """
    Compute Debt-to-Equity Ratio.

    Formula:
        Borrowings / (Equity Capital + Reserves)

    Rules:
    - Return 0 if borrowings == 0
    - Return None if equity + reserves <= 0
    """

    if borrowings == 0:
        return 0

    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return borrowings / equity

def net_profit_margin(net_profit, sales):
    """
    Net Profit Margin (%)

    Formula:
        Net Profit / Sales × 100
    """
    if sales == 0:
        return None

    return round((net_profit / sales) * 100, 2)


def operating_profit_margin(operating_profit, sales):
    """
    Operating Profit Margin (%)

    Formula:
        Operating Profit / Sales × 100
    """
    if sales == 0:
        return None

    return round((operating_profit / sales) * 100, 2)


def return_on_equity(net_profit, equity_capital, reserves):
    """
    Return on Equity (%)

    Formula:
        Net Profit / (Equity Capital + Reserves) × 100
    """
    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return round((net_profit / equity) * 100, 2)