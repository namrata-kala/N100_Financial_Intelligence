import re


def normalize_ticker(ticker):
    """
    Normalize NSE ticker symbols.
    """

    if ticker is None:
        return None

    ticker = str(ticker).strip().upper()

    return ticker


def normalize_year(year):
    """
    Convert financial year strings into YYYY-MM format.

    Examples

    Mar 2024 -> 2024-03
    Dec 2012 -> 2012-12
    2024 -> 2024
    """

    if year is None:
        return None

    year = str(year).strip()

    months = {
        "JAN": "01",
        "FEB": "02",
        "MAR": "03",
        "APR": "04",
        "MAY": "05",
        "JUN": "06",
        "JUL": "07",
        "AUG": "08",
        "SEP": "09",
        "OCT": "10",
        "NOV": "11",
        "DEC": "12",
    }

    if re.fullmatch(r"\d{4}", year):
        return year

    parts = year.split()

    if len(parts) == 2:

        month = months.get(parts[0].upper())

        if month:

            return f"{parts[1]}-{month}"

    return year