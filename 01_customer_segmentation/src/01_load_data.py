"""
01_load_data.py
---------------
Loads the UCI Online Retail II Excel file into the
raw_transactions PostgreSQL table.

Run order: 1st
Prerequisite: sql/01_create_schema.sql must have been run first.

Usage:
    python src/01_load_data.py

Dataset:
    Download 'online_retail_II.xlsx' from:
    https://archive.ics.uci.edu/dataset/502/online+retail+ii
    Place it in the project root folder.
"""

import pandas as pd
from sqlalchemy import create_engine, text
import os

# ── Database connection ────────────────────────────────────────
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/retail_db"
)

# ── Config ─────────────────────────────────────────────────────
EXCEL_FILE  = "online_retail_II.xlsx"
SHEET_NAME  = "Year 2010-2011"
TABLE_NAME  = "raw_transactions"
CHUNK_SIZE  = 10_000


def load_data():
    print(f"Loading '{EXCEL_FILE}' — sheet: '{SHEET_NAME}' ...")

    if not os.path.exists(EXCEL_FILE):
        raise FileNotFoundError(
            f"'{EXCEL_FILE}' not found in project root.\n"
            "Download from: https://archive.ics.uci.edu/dataset/502/online+retail+ii"
        )

    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
    print(f"  Rows loaded from Excel : {len(df):,}")
    print(f"  Columns                : {list(df.columns)}")

    # Rename columns to match PostgreSQL table schema
    df.columns = [
        "invoice_no", "stock_code", "description",
        "quantity", "invoice_date", "unit_price",
        "customer_id", "country"
    ]

    # Convert types
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])
    df["quantity"]     = pd.to_numeric(df["quantity"],   errors="coerce")
    df["unit_price"]   = pd.to_numeric(df["unit_price"], errors="coerce")
    df["customer_id"]  = df["customer_id"].astype(str).str.strip()
    df["customer_id"]  = df["customer_id"].replace("nan", None)

    print(f"  Writing to PostgreSQL table '{TABLE_NAME}' ...")
    engine = create_engine(DB_URL)

    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {TABLE_NAME}"))

    df.to_sql(
        TABLE_NAME,
        engine,
        if_exists="append",
        index=False,
        chunksize=CHUNK_SIZE,
        method="multi"
    )

    with engine.connect() as conn:
        count = conn.execute(
            text(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        ).scalar()

    print(f"  Rows inserted into '{TABLE_NAME}': {count:,}")
    print("  load_data.py complete.\n")


if __name__ == "__main__":
    load_data()
