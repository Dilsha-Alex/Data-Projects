"""
02_clean_and_rfm.py
-------------------
Reads raw_transactions from PostgreSQL, applies cleaning rules,
computes RFM metrics and segment labels, writes results back to
cleaned_transactions and rfm_scores tables.

Run order: 2nd (after 01_load_data.py)

Usage:
    python src/02_clean_and_rfm.py
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import os

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/retail_db"
)
SNAPSHOT_DATE = pd.Timestamp("2011-12-10")


# ── Step 1: Load and clean ─────────────────────────────────────
def clean_transactions(engine):
    print("Loading raw_transactions from PostgreSQL ...")
    df = pd.read_sql("SELECT * FROM raw_transactions", engine)
    print(f"  Raw rows: {len(df):,}")

    # Remove cancellations
    df = df[~df["invoice_no"].astype(str).str.startswith("C")]
    # Remove missing customer IDs
    df = df[df["customer_id"].notna() & (df["customer_id"] != "")]
    # Remove invalid quantity / price
    df = df[(df["quantity"] > 0) & (df["unit_price"] > 0)]
    # UK only
    df = df[df["country"] == "United Kingdom"]
    # Remove test/manual entries
    bad_codes = {"M", "BANK CHARGES", "POST", "D", "DOT"}
    df = df[~df["stock_code"].isin(bad_codes)]
    df = df[~df["description"].str.contains("test", case=False, na=False)]

    df["invoice_date"] = pd.to_datetime(df["invoice_date"]).dt.date
    df["line_revenue"]  = (df["quantity"] * df["unit_price"]).round(2)

    print(f"  Cleaned rows : {len(df):,}")
    print(f"  Unique customers: {df['customer_id'].nunique():,}")

    # Write to cleaned_transactions
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE cleaned_transactions"))
    df.to_sql("cleaned_transactions", engine, if_exists="append",
              index=False, chunksize=10_000, method="multi")
    print("  Written to cleaned_transactions.\n")
    return df


# ── Step 2: Compute RFM metrics ────────────────────────────────
def compute_rfm(df):
    print("Computing RFM metrics ...")
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])

    rfm = (
        df.groupby("customer_id")
        .agg(
            last_purchase  = ("invoice_date", "max"),
            frequency      = ("invoice_no",   "nunique"),
            monetary_value = ("line_revenue",  "sum")
        )
        .reset_index()
    )
    rfm["recency_days"]   = (SNAPSHOT_DATE - rfm["last_purchase"]).dt.days
    rfm["monetary_value"] = rfm["monetary_value"].round(2)
    rfm = rfm.drop(columns=["last_purchase"])
    print(f"  RFM table: {len(rfm):,} customers")
    return rfm


# ── Step 3: Score and segment ──────────────────────────────────
def score_and_segment(rfm):
    print("Scoring RFM metrics ...")

    # R: lower recency = better → reversed labels
    rfm["r_score"] = pd.qcut(
        rfm["recency_days"], q=4, labels=[4, 3, 2, 1], duplicates="drop"
    ).astype(int)

    # F: higher = better
    rfm["f_score"] = pd.qcut(
        rfm["frequency"].rank(method="first"), q=4,
        labels=[1, 2, 3, 4], duplicates="drop"
    ).astype(int)

    # M: higher = better
    rfm["m_score"] = pd.qcut(
        rfm["monetary_value"], q=4, labels=[1, 2, 3, 4], duplicates="drop"
    ).astype(int)

    rfm["rfm_total"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]
    rfm["rfm_code"]  = (rfm["r_score"].astype(str)
                        + rfm["f_score"].astype(str)
                        + rfm["m_score"].astype(str))

    def label(score):
        if score >= 10: return "Champions"
        elif score >= 7: return "Loyal"
        elif score >= 4: return "At-Risk"
        return "Dormant"

    rfm["segment"] = rfm["rfm_total"].apply(label)

    print("  Segment distribution:")
    print(rfm["segment"].value_counts().to_string())
    return rfm


# ── Step 4: Write rfm_scores to DB ────────────────────────────
def write_rfm(rfm, engine):
    cols = ["customer_id", "recency_days", "frequency", "monetary_value",
            "r_score", "f_score", "m_score", "rfm_total", "rfm_code", "segment"]
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE rfm_scores"))
    rfm[cols].to_sql("rfm_scores", engine, if_exists="append",
                     index=False, method="multi")
    print("  Written to rfm_scores.\n")


if __name__ == "__main__":
    engine = create_engine(DB_URL)
    df     = clean_transactions(engine)
    rfm    = compute_rfm(df)
    rfm    = score_and_segment(rfm)
    write_rfm(rfm, engine)
    print("02_clean_and_rfm.py complete.")
