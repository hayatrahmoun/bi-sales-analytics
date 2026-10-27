"""Load the clean star schema into an in-memory SQLite database and run sql/kpi_queries.sql.

Run:  python src/run_sql.py
"""
import re
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"

con = sqlite3.connect(":memory:")
for table in ["fact_sales", "dim_customer", "dim_product", "dim_date"]:
    pd.read_csv(CLEAN / f"{table}.csv").to_sql(table, con, index=False)

sql_text = (ROOT / "sql" / "kpi_queries.sql").read_text(encoding="utf-8")
blocks = re.split(r"^-- name: ", sql_text, flags=re.MULTILINE)[1:]

pd.set_option("display.width", 140)
pd.set_option("display.max_columns", 20)
for block in blocks:
    name, _, query = block.partition("\n")
    print(f"\n=== {name.strip()} ===")
    print(pd.read_sql_query(query, con).to_string(index=False))
