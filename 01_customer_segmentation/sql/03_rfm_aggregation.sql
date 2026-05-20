-- ============================================================
-- 03_rfm_aggregation.sql
-- Computes RFM metrics per customer, assigns quartile scores,
-- maps to segment labels, inserts into rfm_scores
-- ============================================================

TRUNCATE TABLE rfm_scores;

WITH rfm_base AS (
    -- Step 1: Raw RFM metrics per customer
    SELECT
        customer_id,
        (DATE '2011-12-10' - MAX(invoice_date))::INTEGER    AS recency_days,
        COUNT(DISTINCT invoice_no)                           AS frequency,
        ROUND(SUM(line_revenue), 2)                          AS monetary_value
    FROM cleaned_transactions
    GROUP BY customer_id
),
rfm_scored AS (
    -- Step 2: Assign quartile scores 1-4
    SELECT
        customer_id,
        recency_days,
        frequency,
        monetary_value,

        -- Recency: lower days = better → reversed
        CASE
            WHEN recency_days <= PERCENTILE_CONT(0.25)
                 WITHIN GROUP (ORDER BY recency_days) OVER () THEN 4
            WHEN recency_days <= PERCENTILE_CONT(0.50)
                 WITHIN GROUP (ORDER BY recency_days) OVER () THEN 3
            WHEN recency_days <= PERCENTILE_CONT(0.75)
                 WITHIN GROUP (ORDER BY recency_days) OVER () THEN 2
            ELSE 1
        END AS r_score,

        -- Frequency: higher = better
        CASE
            WHEN frequency >= PERCENTILE_CONT(0.75)
                 WITHIN GROUP (ORDER BY frequency) OVER () THEN 4
            WHEN frequency >= PERCENTILE_CONT(0.50)
                 WITHIN GROUP (ORDER BY frequency) OVER () THEN 3
            WHEN frequency >= PERCENTILE_CONT(0.25)
                 WITHIN GROUP (ORDER BY frequency) OVER () THEN 2
            ELSE 1
        END AS f_score,

        -- Monetary: higher = better
        CASE
            WHEN monetary_value >= PERCENTILE_CONT(0.75)
                 WITHIN GROUP (ORDER BY monetary_value) OVER () THEN 4
            WHEN monetary_value >= PERCENTILE_CONT(0.50)
                 WITHIN GROUP (ORDER BY monetary_value) OVER () THEN 3
            WHEN monetary_value >= PERCENTILE_CONT(0.25)
                 WITHIN GROUP (ORDER BY monetary_value) OVER () THEN 2
            ELSE 1
        END AS m_score

    FROM rfm_base
),
rfm_labelled AS (
    -- Step 3: Composite score and segment label
    SELECT
        *,
        (r_score + f_score + m_score)                           AS rfm_total,
        CONCAT(r_score::TEXT, f_score::TEXT, m_score::TEXT)     AS rfm_code,
        CASE
            WHEN (r_score + f_score + m_score) >= 10 THEN 'Champions'
            WHEN (r_score + f_score + m_score) >= 7  THEN 'Loyal'
            WHEN (r_score + f_score + m_score) >= 4  THEN 'At-Risk'
            ELSE 'Dormant'
        END AS segment
    FROM rfm_scored
)
INSERT INTO rfm_scores
SELECT
    customer_id, recency_days, frequency, monetary_value,
    r_score, f_score, m_score, rfm_total, rfm_code, segment
FROM rfm_labelled;

-- ── Summary output ────────────────────────────────────────────
SELECT
    segment,
    COUNT(*)                            AS customers,
    ROUND(AVG(recency_days),  1)        AS avg_recency_days,
    ROUND(AVG(frequency),     1)        AS avg_orders,
    ROUND(AVG(monetary_value),2)        AS avg_spend,
    ROUND(SUM(monetary_value),2)        AS total_revenue,
    ROUND(
        SUM(monetary_value) * 100.0 /
        SUM(SUM(monetary_value)) OVER (), 1
    )                                   AS revenue_share_pct
FROM rfm_scores
GROUP BY segment
ORDER BY total_revenue DESC;
