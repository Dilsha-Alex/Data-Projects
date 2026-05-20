"""
05_export_tableau_data.py
-------------------------
Exports analysis-ready CSV files from PostgreSQL to
outputs/tableau_exports/ for use in Tableau Public.

Run order: 5th (final step — after all analysis scripts)

Usage:
    python src/05_export_tableau_data.py

Tableau Public setup:
    1. Open Tableau Public Desktop
    2. Connect → Text File → select each CSV from outputs/tableau_exports/
    3. Build visualisations as described in README.md
    4. Publish to Tableau Public and paste your link in README.md
"""

import pandas as pd
from sqlalchemy import create_engine
import os

DB_URL     = os.getenv("DATABASE_URL",
             "postgresql://postgres:password@localhost:5432/retail_db")
EXPORT_DIR = "outputs/tableau_exports"
os.makedirs(EXPORT_DIR, exist_ok=True)


def export(engine):

    # ── 1. Full RFM scores with segments ──────────────────────
    rfm = pd.read_sql("SELECT * FROM rfm_scores ORDER BY segment, monetary_value DESC", engine)
    path = f"{EXPORT_DIR}/rfm_segments.csv"
    rfm.to_csv(path, index=False)
    print(f"Exported: {path}  ({len(rfm):,} rows)")

    # ── 2. Segment summary ────────────────────────────────────
    summary = rfm.groupby("segment").agg(
        customer_count  = ("customer_id",    "count"),
        avg_recency     = ("recency_days",   "mean"),
        avg_frequency   = ("frequency",      "mean"),
        avg_monetary    = ("monetary_value", "mean"),
        total_revenue   = ("monetary_value", "sum")
    ).round(2).reset_index()
    total = summary["total_revenue"].sum()
    summary["revenue_share_pct"]  = (summary["total_revenue"] / total * 100).round(1)
    summary["customer_share_pct"] = (summary["customer_count"] / summary["customer_count"].sum() * 100).round(1)
    path = f"{EXPORT_DIR}/segment_summary.csv"
    summary.to_csv(path, index=False)
    print(f"Exported: {path}  ({len(summary)} rows)")

    # ── 3. Cohort retention heatmap data ─────────────────────
    cohort = pd.read_sql(
        "SELECT * FROM cohort_retention ORDER BY cohort_month, cohort_index", engine
    )
    path = f"{EXPORT_DIR}/cohort_retention.csv"
    cohort.to_csv(path, index=False)
    print(f"Exported: {path}  ({len(cohort):,} rows)")

    # ── 4. Average retention curve ────────────────────────────
    avg_ret = cohort.groupby("cohort_index").agg(
        avg_retention = ("retention_pct", "mean"),
        min_retention = ("retention_pct", "min"),
        max_retention = ("retention_pct", "max")
    ).round(2).reset_index()
    avg_ret.columns = ["months_since_acquisition",
                       "avg_retention_pct", "min_retention_pct", "max_retention_pct"]
    path = f"{EXPORT_DIR}/avg_retention_curve.csv"
    avg_ret.to_csv(path, index=False)
    print(f"Exported: {path}  ({len(avg_ret)} rows)")

    print(f"\nAll files saved to: {EXPORT_DIR}/")
    print("\nNext steps:")
    print("  1. Open Tableau Public Desktop")
    print("  2. Connect to each CSV in outputs/tableau_exports/")
    print("  3. Build dashboards using instructions in README.md")
    print("  4. Publish and paste your Tableau Public link into README.md")


if __name__ == "__main__":
    engine = create_engine(DB_URL)
    export(engine)
    print("\n05_export_tableau_data.py complete.")
