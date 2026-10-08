-- question: growth
WITH lagged AS (
    SELECT *, LAG(gross_sales) OVER (ORDER BY month) AS previous_sales,
              LAG(complete_month) OVER (ORDER BY month) AS previous_complete
    FROM v_monthly
)
SELECT month, gross_sales, complete_month,
       CASE WHEN complete_month = 1 AND previous_complete = 1
            THEN gross_sales / NULLIF(previous_sales, 0) - 1 END AS mom_growth
FROM lagged ORDER BY month;

-- question: yoy
SELECT current.month, current.gross_sales, prior.gross_sales AS previous_year_sales,
       current.gross_sales / NULLIF(prior.gross_sales, 0) - 1 AS yoy_growth
FROM v_monthly current JOIN v_monthly prior
  ON prior.month = STRFTIME('%Y-%m', DATE(current.month || '-01', '-1 year'))
WHERE current.complete_month = 1 AND prior.complete_month = 1 ORDER BY current.month;

-- question: rolling
SELECT date, gross_sales,
       AVG(gross_sales) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
           AS moving_7_day_sales,
       SUM(gross_sales) OVER (ORDER BY date) AS running_sales
FROM v_daily ORDER BY date;

-- question: concentration
WITH totals AS (
    SELECT customer_id, SUM(gross_sales) AS gross_sales FROM fact_sales
    WHERE customer_id <> 'UNKNOWN' AND is_sale = 1 GROUP BY customer_id
), ranked AS (
    SELECT *, ROW_NUMBER() OVER (ORDER BY gross_sales DESC) AS rank,
           SUM(gross_sales) OVER () AS total_known_sales FROM totals
)
SELECT rank, customer_id, gross_sales, gross_sales / total_known_sales AS share,
       SUM(gross_sales) OVER (ORDER BY rank) / total_known_sales AS cumulative_share
FROM ranked ORDER BY rank LIMIT 100;

-- question: repeat
WITH customers AS (
    SELECT customer_id, COUNT(DISTINCT invoice_id) AS orders, SUM(gross_sales) AS gross_sales
    FROM fact_sales WHERE customer_id <> 'UNKNOWN' AND is_sale = 1 GROUP BY customer_id
)
SELECT CASE WHEN orders = 1 THEN 'One observed invoice' ELSE 'Multiple observed invoices' END
           AS segment,
       COUNT(*) AS customers, SUM(gross_sales) AS gross_sales
FROM customers GROUP BY segment;

-- question: cohorts
WITH active AS (
    SELECT DISTINCT customer_id, SUBSTR(date, 1, 7) AS month
    FROM fact_sales WHERE customer_id <> 'UNKNOWN' AND is_sale = 1
), firsts AS (
    SELECT customer_id, MIN(month) AS cohort FROM active GROUP BY customer_id
), cohort_sizes AS (
    SELECT cohort, COUNT(*) AS initial_customers FROM firsts GROUP BY cohort
)
SELECT f.cohort, a.month,
       (CAST(SUBSTR(a.month, 1, 4) AS INTEGER) - CAST(SUBSTR(f.cohort, 1, 4) AS INTEGER)) * 12
       + CAST(SUBSTR(a.month, 6, 2) AS INTEGER) - CAST(SUBSTR(f.cohort, 6, 2) AS INTEGER)
           AS months_since_first,
       COUNT(*) AS active_customers, s.initial_customers,
       1.0 * COUNT(*) / s.initial_customers AS observed_retention
FROM active a JOIN firsts f USING (customer_id) JOIN cohort_sizes s USING (cohort)
GROUP BY f.cohort, a.month, s.initial_customers ORDER BY f.cohort, a.month;

-- question: rfm
WITH customers AS (
    SELECT customer_id, MAX(date) AS last_purchase, COUNT(DISTINCT invoice_id) AS frequency,
           SUM(gross_sales) AS monetary
    FROM fact_sales WHERE customer_id <> 'UNKNOWN' AND is_sale = 1 GROUP BY customer_id
)
SELECT customer_id,
       JULIANDAY((SELECT MAX(date) FROM dim_date)) - JULIANDAY(last_purchase) AS recency_days,
       frequency, monetary,
       NTILE(4) OVER (ORDER BY monetary) AS monetary_quartile
FROM customers ORDER BY monetary DESC;

-- question: zero_days
SELECT date, weekday, recorded_lines, gross_sales FROM v_daily
WHERE gross_sales = 0 ORDER BY date;

-- question: contributions
WITH c AS (
    SELECT p.product_id, p.description, SUM(f.gross_sales) AS gross_sales
    FROM fact_sales f JOIN dim_product p USING(product_id)
    GROUP BY p.product_id, p.description
)
SELECT *, gross_sales / SUM(gross_sales) OVER () AS sales_share,
       SUM(gross_sales) OVER (ORDER BY gross_sales DESC, product_id) / SUM(gross_sales) OVER ()
           AS cumulative_share
FROM c ORDER BY gross_sales DESC, product_id;

