-- ============================================================
-- 02_clean_data.sql
-- Cleans raw_transactions → cleaned_transactions
-- Removes: cancellations, null CustomerIDs, invalid qty/price,
--          non-UK records, test/manual entries
-- ============================================================

TRUNCATE TABLE cleaned_transactions;

INSERT INTO cleaned_transactions (
    invoice_no, stock_code, description,
    quantity, invoice_date, unit_price,
    customer_id, country, line_revenue
)
SELECT
    invoice_no,
    stock_code,
    description,
    quantity,
    invoice_date::DATE,
    unit_price,
    customer_id,
    country,
    ROUND(quantity * unit_price, 2)   AS line_revenue
FROM raw_transactions
WHERE
    invoice_no  NOT LIKE 'C%'                          -- remove cancellations
    AND customer_id IS NOT NULL
    AND customer_id <> ''
    AND quantity    > 0
    AND unit_price  > 0
    AND country     = 'United Kingdom'
    AND stock_code  NOT IN ('M','BANK CHARGES','POST','D','DOT')
    AND description NOT ILIKE '%test%';

-- ── Validation report ─────────────────────────────────────────
SELECT
    'raw_transactions'      AS source,
    COUNT(*)                AS row_count
FROM raw_transactions
UNION ALL
SELECT
    'cleaned_transactions',
    COUNT(*)
FROM cleaned_transactions;

-- Check no nulls remain on critical columns
SELECT
    SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_customers,
    SUM(CASE WHEN quantity    <= 0    THEN 1 ELSE 0 END) AS bad_quantity,
    SUM(CASE WHEN unit_price  <= 0    THEN 1 ELSE 0 END) AS bad_price
FROM cleaned_transactions;

-- Date range and unique customer count
SELECT
    MIN(invoice_date)               AS earliest_date,
    MAX(invoice_date)               AS latest_date,
    COUNT(DISTINCT customer_id)     AS unique_customers,
    COUNT(DISTINCT invoice_no)      AS unique_invoices,
    ROUND(SUM(line_revenue), 2)     AS total_revenue
FROM cleaned_transactions;
