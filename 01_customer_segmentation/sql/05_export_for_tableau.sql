-- ============================================================
-- 05_export_for_tableau.sql
-- Exports analysis-ready CSVs for Tableau Public visualisations
-- Run after 03_rfm_aggregation.sql and 04_cohort_analysis.sql
--
-- Usage (psql):
--   \i 05_export_for_tableau.sql
-- Or run via Python export script: src/05_export_tableau_data.py
-- ============================================================

-- ── Export 1: RFM scores with segment labels ─────────────────
-- Used for: scatter plot, segment bar charts, KPI cards
COPY (
    SELECT
        customer_id,
        recency_days,
        frequency,
        monetary_value,
        r_score,
        f_score,
        m_score,
        rfm_total,
        rfm_code,
        segment
    FROM rfm_scores
    ORDER BY segment, monetary_value DESC
)
TO '/tmp/rfm_segments.csv'
WITH (FORMAT CSV, HEADER TRUE);

-- ── Export 2: Segment summary ─────────────────────────────────
-- Used for: KPI tiles, revenue share donut, bar chart
COPY (
    SELECT
        segment,
        COUNT(*)                                AS customer_count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)
                                                AS customer_pct,
        ROUND(AVG(recency_days),  1)            AS avg_recency_days,
        ROUND(AVG(frequency),     1)            AS avg_orders,
        ROUND(AVG(monetary_value),2)            AS avg_spend,
        ROUND(SUM(monetary_value),2)            AS total_revenue,
        ROUND(SUM(monetary_value) * 100.0 /
              SUM(SUM(monetary_value)) OVER (), 1)
                                                AS revenue_share_pct
    FROM rfm_scores
    GROUP BY segment
    ORDER BY total_revenue DESC
)
TO '/tmp/segment_summary.csv'
WITH (FORMAT CSV, HEADER TRUE);

-- ── Export 3: Cohort retention table ─────────────────────────
-- Used for: cohort heatmap
COPY (
    SELECT
        cohort_month,
        cohort_index,
        customer_count,
        retention_pct
    FROM cohort_retention
    ORDER BY cohort_month, cohort_index
)
TO '/tmp/cohort_retention.csv'
WITH (FORMAT CSV, HEADER TRUE);

-- ── Export 4: Average retention curve ────────────────────────
-- Used for: line chart of retention decay
COPY (
    SELECT
        cohort_index                        AS months_since_acquisition,
        ROUND(AVG(retention_pct), 1)        AS avg_retention_pct,
        ROUND(MIN(retention_pct), 1)        AS min_retention_pct,
        ROUND(MAX(retention_pct), 1)        AS max_retention_pct
    FROM cohort_retention
    GROUP BY cohort_index
    ORDER BY cohort_index
)
TO '/tmp/avg_retention_curve.csv'
WITH (FORMAT CSV, HEADER TRUE);

SELECT 'Exports complete. Files written to /tmp/' AS status;
