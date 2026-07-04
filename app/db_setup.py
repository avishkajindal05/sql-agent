"""Creates and seeds the SQLite orders database."""

import sqlite3
from pathlib import Path

DB_PATH = "data/orders.db"


def create_db(path: str = DB_PATH) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            customer_name TEXT NOT NULL,
            product TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            order_date TEXT NOT NULL,
            region TEXT NOT NULL
        )
    """)

    sample_rows: list[tuple[int, str, str, int, float, str, str]] = [
        (1, "Ravi Kumar", "Laptop", 1, 55000.0, "2026-01-15", "North"),
        (2, "Ayesha Khan", "Mouse", 3, 500.0, "2026-01-20", "South"),
        (3, "Rahul Verma", "Monitor", 2, 8000.0, "2026-02-05", "West"),
        (4, "Sneha Iyer", "Laptop", 1, 55000.0, "2026-03-10", "South"),
        (5, "Aman Gupta", "Keyboard", 5, 700.0, "2026-03-18", "North"),
        (6, "Priya Nair", "Monitor", 1, 8000.0, "2026-03-22", "East"),
        (7, "Vikram Singh", "Laptop", 2, 55000.0, "2026-04-02", "North"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO orders VALUES (?,?,?,?,?,?,?)", sample_rows
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_db()
    print(f"Database created at {DB_PATH}")
