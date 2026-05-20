"""
04_kmeans_clustering.py
-----------------------
Applies K-Means clustering (k=4) to normalised RFM values
to validate score-based segments against natural data groupings.
Generates elbow and silhouette charts saved to outputs/.

Run order: 4th (after 02_clean_and_rfm.py)

Usage:
    python src/04_kmeans_clustering.py
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sqlalchemy import create_engine
import os

DB_URL      = os.getenv("DATABASE_URL",
              "postgresql://postgres:password@localhost:5432/retail_db")
OUTPUT_DIR  = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

PALETTE = {
    "Champions": "#1F4E79",
    "Loyal":     "#2E75B6",
    "At-Risk":   "#F4A300",
    "Dormant":   "#C0392B"
}
SEGMENT_ORDER = ["Champions", "Loyal", "At-Risk", "Dormant"]


def run_kmeans():
    engine = create_engine(DB_URL)
    rfm = pd.read_sql("SELECT * FROM rfm_scores", engine)
    print(f"Loaded {len(rfm):,} customers from rfm_scores.")

    features = ["recency_days", "frequency", "monetary_value"]
    scaler   = MinMaxScaler()
    X        = scaler.fit_transform(rfm[features])
    X[:, 0]  = 1 - X[:, 0]          # invert recency: higher = more recent

    # ── Elbow + Silhouette ─────────────────────────────────────
    inertia, sil = [], []
    K = range(2, 9)
    for k in K:
        km  = KMeans(n_clusters=k, random_state=42, n_init=10)
        lbl = km.fit_predict(X)
        inertia.append(km.inertia_)
        sil.append(silhouette_score(X, lbl))

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    fig.patch.set_facecolor("#F8FBFF")
    for ax, vals, title, ylabel in zip(
        axes,
        [inertia, sil],
        ["Elbow Method — Inertia", "Silhouette Score by k"],
        ["Inertia", "Silhouette Score"]
    ):
        ax.set_facecolor("#F8FBFF")
        ax.plot(K, vals, "o-", color="#1F4E79", linewidth=2)
        ax.axvline(x=4, color="#F4A300", linestyle="--", alpha=0.8,
                   label="k=4 chosen")
        ax.set_title(title, fontweight="bold", color="#1F4E79")
        ax.set_xlabel("k"); ax.set_ylabel(ylabel)
        ax.legend(fontsize=9)
        ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    path = f"{OUTPUT_DIR}/kmeans_elbow_silhouette.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")
    print(f"  Silhouette at k=4: {sil[2]:.3f}")

    # ── Fit final k=4 ─────────────────────────────────────────
    km4    = KMeans(n_clusters=4, random_state=42, n_init=10)
    rfm["cluster"] = km4.fit_predict(X)

    centroids = rfm.groupby("cluster")[features].mean().round(2)
    centroids["size"] = rfm.groupby("cluster").size()
    print("\nCluster centroids:")
    print(centroids.to_string())

    # ── Segment distribution chart ─────────────────────────────
    seg = rfm.groupby("segment").agg(
        count=("customer_id", "count"),
        revenue=("monetary_value", "sum")
    ).reindex(SEGMENT_ORDER)
    seg["cust_pct"] = (seg["count"]   / seg["count"].sum()   * 100).round(1)
    seg["rev_pct"]  = (seg["revenue"] / seg["revenue"].sum() * 100).round(1)

    colors = [PALETTE[s] for s in SEGMENT_ORDER]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.patch.set_facecolor("#F8FBFF")
    for ax, col, ylabel, title in zip(
        axes,
        ["cust_pct", "rev_pct"],
        ["% of Customers", "% of Revenue"],
        ["Customer Distribution", "Revenue Contribution"]
    ):
        ax.set_facecolor("#F8FBFF")
        bars = ax.bar(SEGMENT_ORDER, seg[col], color=colors,
                      width=0.55, edgecolor="white", linewidth=1.5)
        ax.set_title(title, fontsize=12, fontweight="bold", color="#1F4E79")
        ax.set_ylabel(ylabel); ax.set_ylim(0, seg[col].max() * 1.2)
        ax.spines[["top", "right"]].set_visible(False)
        for bar, val in zip(bars, seg[col]):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
                    f"{val:.0f}%", ha="center", fontweight="bold",
                    fontsize=11, color="#1F4E79")
    fig.suptitle("RFM Segment Overview", fontsize=14,
                 fontweight="bold", color="#1F4E79")
    plt.tight_layout()
    path2 = f"{OUTPUT_DIR}/segment_distribution.png"
    plt.savefig(path2, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path2}")


if __name__ == "__main__":
    run_kmeans()
    print("\n04_kmeans_clustering.py complete.")
