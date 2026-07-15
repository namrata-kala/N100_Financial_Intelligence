from src.etl.normaliser import normalize_year
from src.etl.normaliser import normalize_ticker

print(normalize_ticker(" abb "))
print(normalize_ticker("tcs"))

print(normalize_year("Mar 2024"))
print(normalize_year("Dec 2012"))
print(normalize_year("2023"))
