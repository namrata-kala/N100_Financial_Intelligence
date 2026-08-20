import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")

print(pd.read_sql(
    "SELECT * FROM financial_ratios LIMIT 5",
    conn
))

conn.close()