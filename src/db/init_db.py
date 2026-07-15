import sqlite3
from pathlib import Path

DB_PATH = Path("db/nifty100.db")
SCHEMA_PATH = Path("db/schema.sql")


def initialize_database():
    conn = sqlite3.connect(DB_PATH)

    conn.execute("PRAGMA foreign_keys = ON;")

    with open(SCHEMA_PATH, "r") as f:
        schema = f.read()

    conn.executescript(schema)

    conn.commit()
    conn.close()

    print("Database initialized successfully!")


if __name__ == "__main__":
    initialize_database()