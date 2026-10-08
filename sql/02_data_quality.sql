-- question: quality
SELECT COUNT(*) AS accepted_lines,
       SUM(CASE WHEN customer_id = 'UNKNOWN' THEN 1 ELSE 0 END) AS anonymous_lines,
       SUM(ambiguous_duplicate) AS ambiguous_repeat_lines,
       SUM(CASE WHEN unit_price = 0 THEN 1 ELSE 0 END) AS zero_price_lines
FROM fact_sales;

-- question: duplicate_sensitivity
WITH business_rows AS (
    SELECT invoice_id, product_id, customer_id, country_id, invoice_date, quantity, unit_price,
           COUNT(*) AS copies, MIN(gross_sales) AS value
    FROM fact_sales
    GROUP BY invoice_id, product_id, customer_id, country_id, invoice_date, quantity, unit_price
)
SELECT SUM(value * copies) AS retained_gross_sales,
       SUM(value) AS hypothetical_deduplicated_sales,
       SUM(value * (copies - 1)) AS ambiguous_value_difference
FROM business_rows;

-- question: adjustments
SELECT SUM(is_adjustment) AS non_cancel_negative_lines,
       SUM(CASE WHEN is_adjustment THEN net_value ELSE 0 END) AS adjustment_value,
       SUM(CASE WHEN is_cancellation AND net_value > 0 THEN 1 ELSE 0 END)
           AS positive_cancellation_lines
FROM fact_sales;

