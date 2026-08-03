def free_cash_flow(
    operating_activity,
    investing_activity,
):
    """
    Free Cash Flow

    Formula:
        Operating Activity + Investing Activity

    Negative values are allowed.
    """

    return operating_activity + investing_activity

def cfo_quality_score(
    operating_activity,
    net_profit,
):
    """
    CFO Quality Score

    Formula:
        CFO / PAT

    Returns:
        (ratio, label)
    """

    if net_profit == 0:
        return None, None

    ratio = operating_activity / net_profit

    if ratio > 1.0:
        label = "High Quality"
    elif ratio >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"

    return round(ratio, 2), label

def capex_intensity(
    investing_activity,
    sales,
):
    """
    CapEx Intensity

    Formula:
        abs(Investing Activity) / Sales × 100

    Returns:
        (percentage, category)
    """

    if sales == 0:
        return None, None

    intensity = abs(investing_activity) / sales * 100

    if intensity < 3:
        category = "Asset Light"
    elif intensity <= 8:
        category = "Moderate"
    else:
        category = "Capital Intensive"

    return round(intensity, 2), category

def fcf_conversion_rate(
    free_cash_flow,
    operating_profit,
):
    """
    FCF Conversion Rate

    Formula:
        FCF / Operating Profit × 100

    Returns:
        Percentage or None if operating profit is zero.
    """

    if operating_profit == 0:
        return None

    rate = (free_cash_flow / operating_profit) * 100

    return round(rate, 2)

def capital_allocation_pattern(
    operating_activity,
    investing_activity,
    financing_activity,
    cfo_quality_label=None,
):
    """
    Classify capital allocation pattern based on
    CFO, CFI and CFF signs.
    """

    cfo = operating_activity >= 0
    cfi = investing_activity >= 0
    cff = financing_activity >= 0

    # (+,-,-)
    if cfo and not cfi and not cff:
        if cfo_quality_label == "High Quality":
            return "Shareholder Returns"
        return "Reinvestor"

    # (+,+,-)
    if cfo and cfi and not cff:
        return "Liquidating Assets"

    # (-,+,+)
    if not cfo and cfi and cff:
        return "Distress Signal"

    # (-,-,+)
    if not cfo and not cfi and cff:
        return "Growth Funded by Debt"

    # (+,+,+)
    if cfo and cfi and cff:
        return "Cash Accumulator"

    # (-,-,-)
    if not cfo and not cfi and not cff:
        return "Pre-Revenue"

    # (+,-,+)
    if cfo and not cfi and cff:
        return "Mixed"

    return "Other"