-- ============================================================
-- 04_cohort_analysis.sql
-- Builds monthly cohort retention table
-- Each cohort = customers grouped by first purchase month
-- Retention = % of cohort still purchasing in each subsequent month
-- ============================================================

TRUNCATE TABLE cohort_retention;

WITH first_purchase AS (
    -- Assign each customer to their acquisition cohort month
    SELECT
        customer_id,
        TO_CHAR(MIN(invoice_date), 'YYYY-MM')   AS cohort_month
    FROM cleaned_transactions
    GROUP BY customer_id
),
customer_activity AS (
    -- All months a customer was active
    SELECT DISTINCT
        t.customer_id,
        TO_CHAR(t.invoice_date, 'YYYY-MM')      AS active_month
    FROM cleaned_transactions t
),
cohort_data AS (
    -- Join activity to cohort, compute months since first purchase
    SELECT
        fp.cohort_month,
        ca.active_month,
        -- Number of months between cohort and activity month
        (DATE_PART('year',  TO_DATE(ca.active_month, 'YYYY-MM')) -
         DATE_PART('year',  TO_DATE(fp.cohort_month, 'YYYY-MM'))) * 12 +
        (DATE_PART('month', TO_DATE(ca.active_month, 'YYYY-MM')) -
         DATE_PART('month', TO_DATE(fp.cohort_month, 'YYYY-MM')))
                                                AS cohort_index,
        COUNT(DISTINCT fp.customer_id)          AS customer_count
    FROM first_purchase fp
    JOIN customer_activity ca USING (customer_id)
    GROUP BY fp.cohort_month, ca.active_month, cohort_index
),
cohort_sizes AS (
    SELECT cohort_month, customer_count AS cohort_size
    FROM cohort_data
    WHERE cohort_index = 0
)
INSERT INTO cohort_retention (cohort_month, cohort_index,
                               customer_count, retention_pct)
SELECT
    cd.cohort_month,
    cd.cohort_index,
    cd.customer_count,
    ROUND(cd.customer_count * 100.0 / cs.cohort_size, 2) AS retention_pct
FROM cohort_data cd
JOIN cohort_sizes cs USING (cohort_month)
ORDER BY cd.cohort_month, cd.cohort_index;

-- ── Preview retention table ───────────────────────────────────
SELECT * FROM cohort_retention
ORDER BY cohort_month, cohort_index
LIMIT 30;

-- ── Average retention by month index ─────────────────────────
SELECT
    cohort_index                            AS months_since_acquisition,
    ROUND(AVG(retention_pct), 1)            AS avg_retention_pct,
    COUNT(*)                                AS cohorts_contributing
FROM cohort_retention
GROUP BY cohort_index
ORDER BY cohort_index;
