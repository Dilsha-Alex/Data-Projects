"""
03_cohort_analysis.py
---------------------
Builds monthly cohort retention table from cleaned_transactions
and writes results to cohort_retention table in PostgreSQL.

Run order: 3rd (after 02_clean_and_rfm.py)

Usage:
    python src/03_cohort_analysis.py
"""

import pandas as pd
from sqlalchemy import create_engine, text
import os

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/retail_db"
)


def build_cohort_table(engine):
    print("Loading cleaned_transactions ...")
    df = pd.read_sql(
        "SELECT customer_id, invoice_no, invoice_date FROM cleaned_transactions",
        engine
    )
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])
    df["order_month"]  = df["invoice_date"].dt.to_period("M")

    # Assign cohort month = first purchase month per customer
    cohort_map = (
        df.groupby("customer_id")["order_month"]
        .min()
        .reset_index()
        .rename(columns={"order_month": "cohort_month"})
    )
    df = df.merge(cohort_map, on="customer_id", how="left")
    df["cohort_index"] = (
        (df["order_month"] - df["cohort_month"]).apply(lambda x: x.n)
    )

    # Count distinct customers per cohort × month index
    counts = (
        df.groupby(["cohort_month", "cohort_index"])["customer_id"]
        .nunique()
        .reset_index()
        .rename(columns={"customer_id": "customer_count"})
    )

    # Cohort sizes (index = 0)
    cohort_sizes = counts[counts["cohort_index"] == 0].set_index("cohort_month")["customer_count"]
    counts["cohort_size"] = counts["cohort_month"].map(cohort_sizes)
    counts["retention_pct"] = (
        counts["customer_count"] / counts["cohort_size"] * 100
    ).round(2)

    counts["cohort_month"] = counts["cohort_month"].astype(str)

    print(f"  Cohorts: {counts['cohort_month'].nunique()}")
    print(f"  Total rows in retention table: {len(counts):,}")

    # Write to DB
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE cohort_retention"))
    counts[["cohort_month", "cohort_index", "customer_count", "retention_pct"]].to_sql(
        "cohort_retention", engine, if_exists="append", index=False, method="multi"
    )
    print("  Written to cohort_retention.\n")
    return counts


def print_avg_retention(engine):
    avg = pd.read_sql("""
        SELECT
            cohort_index        AS months_since_acquisition,
            ROUND(AVG(retention_pct)::NUMERIC, 1)   AS avg_retention_pct
        FROM cohort_retention
        GROUP BY cohort_index
        ORDER BY cohort_index
        LIMIT 13
    """, engine)
    print("Average retention by month index:")
    print(avg.to_string(index=False))


if __name__ == "__main__":
    engine = create_engine(DB_URL)
    build_cohort_table(engine)
    print_avg_retention(engine)
    print("\n03_cohort_analysis.py complete.")
