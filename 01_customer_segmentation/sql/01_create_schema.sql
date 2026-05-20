-- ============================================================
-- 01_create_schema.sql
-- Creates all tables for the Customer Segmentation project
-- Database: PostgreSQL 15+
-- Run this first before any other script
-- ============================================================

-- Drop tables if re-running
DROP TABLE IF EXISTS rfm_scores CASCADE;
DROP TABLE IF EXISTS cleaned_transactions CASCADE;
DROP TABLE IF EXISTS raw_transactions CASCADE;

-- ── Raw transactions (loaded from UCI Excel file via Python) ──
CREATE TABLE raw_transactions (
    invoice_no      VARCHAR(20),
    stock_code      VARCHAR(20),
    description     VARCHAR(255),
    quantity        INTEGER,
    invoice_date    TIMESTAMP,
    unit_price      NUMERIC(10, 2),
    customer_id     VARCHAR(20),
    country         VARCHAR(100)
);

-- ── Cleaned transactions (populated by 02_clean_data.sql) ────
CREATE TABLE cleaned_transactions (
    invoice_no      VARCHAR(20),
    stock_code      VARCHAR(20),
    description     VARCHAR(255),
    quantity        INTEGER,
    invoice_date    DATE,
    unit_price      NUMERIC(10, 2),
    customer_id     VARCHAR(20),
    country         VARCHAR(100),
    line_revenue    NUMERIC(12, 2)
);

-- ── RFM scores (populated by 03_rfm_aggregation.sql) ─────────
CREATE TABLE rfm_scores (
    customer_id         VARCHAR(20) PRIMARY KEY,
    recency_days        INTEGER,
    frequency           INTEGER,
    monetary_value      NUMERIC(12, 2),
    r_score             SMALLINT,
    f_score             SMALLINT,
    m_score             SMALLINT,
    rfm_total           SMALLINT,
    rfm_code            VARCHAR(3),
    segment             VARCHAR(20)
);

-- ── Cohort retention (populated by 04_cohort_analysis.sql) ───
CREATE TABLE cohort_retention (
    cohort_month        VARCHAR(10),
    cohort_index        INTEGER,
    customer_count      INTEGER,
    retention_pct       NUMERIC(5, 2)
);

COMMENT ON TABLE raw_transactions    IS 'Raw UCI Online Retail II data loaded via Python';
COMMENT ON TABLE cleaned_transactions IS 'Filtered: no cancellations, nulls, negatives, UK only';
COMMENT ON TABLE rfm_scores          IS 'RFM metrics and segment labels per customer';
COMMENT ON TABLE cohort_retention    IS 'Monthly cohort retention rates for heatmap';

SELECT 'Schema created successfully.' AS status;
