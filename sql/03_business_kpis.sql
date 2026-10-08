-- question: overview
SELECT SUM(gross_sales) AS gross_sales, SUM(net_value) AS signed_value,
       SUM(cancellation_value) AS cancellation_value,
       COUNT(DISTINCT CASE WHEN is_sale THEN invoice_id END) AS sale_invoices,
       COUNT(DISTINCT CASE WHEN customer_id <> 'UNKNOWN' AND is_sale THEN customer_id END)
           AS known_buyers,
       SUM(gross_sales) / NULLIF(COUNT(DISTINCT CASE WHEN is_sale THEN invoice_id END), 0)
           AS average_invoice_gbp
FROM fact_sales;

-- question: monthly
SELECT * FROM v_monthly ORDER BY month;

-- question: country
SELECT c.country, SUM(f.gross_sales) AS gross_sales,
       COUNT(DISTINCT CASE WHEN f.is_sale THEN f.invoice_id END) AS orders,
       SUM(f.gross_sales) / SUM(SUM(f.gross_sales)) OVER () AS share
FROM fact_sales f JOIN dim_country c USING (country_id)
GROUP BY c.country ORDER BY gross_sales DESC;

-- question: products
SELECT p.product_id, p.description, SUM(f.gross_sales) AS gross_sales,
       SUM(CASE WHEN f.is_sale THEN f.quantity ELSE 0 END) AS sale_units,
       DENSE_RANK() OVER (ORDER BY SUM(f.gross_sales) DESC) AS revenue_rank
FROM fact_sales f JOIN dim_product p USING (product_id)
GROUP BY p.product_id, p.description ORDER BY gross_sales DESC LIMIT 30;

-- question: cancellation_country
SELECT c.country, SUM(f.cancellation_value) AS cancellation_value,
       SUM(f.gross_sales) AS gross_sales,
       SUM(f.cancellation_value) / NULLIF(SUM(f.gross_sales), 0) AS value_ratio
FROM fact_sales f JOIN dim_country c USING (country_id)
GROUP BY c.country HAVING SUM(f.gross_sales) > 0 ORDER BY cancellation_value DESC;

-- question: anonymous
SELECT CASE WHEN customer_id = 'UNKNOWN' THEN 'Anonymous' ELSE 'Identified' END AS segment,
       COUNT(*) AS lines, SUM(gross_sales) AS gross_sales,
       SUM(gross_sales) / SUM(SUM(gross_sales)) OVER () AS sales_share
FROM fact_sales GROUP BY segment;

-- question: baskets
SELECT c.country, COUNT(*) AS invoice_groups, AVG(i.gross_sales) AS average_invoice_gbp,
       AVG(i.sale_lines) AS average_lines, AVG(i.sale_units) AS average_units
FROM v_invoices i JOIN dim_country c USING (country_id)
WHERE i.gross_sales > 0 GROUP BY c.country ORDER BY invoice_groups DESC;

-- question: weekday
SELECT weekday, COUNT(*) AS calendar_days, AVG(gross_sales) AS average_daily_sales,
       AVG(orders) AS average_orders FROM v_daily
GROUP BY weekday ORDER BY weekday;

-- question: hourly
SELECT hour, SUM(gross_sales) AS gross_sales, SUM(is_sale) AS sale_lines
FROM fact_sales GROUP BY hour ORDER BY hour;

-- question: prices
SELECT product_id, MIN(unit_price) AS min_price, MAX(unit_price) AS max_price,
       COUNT(DISTINCT unit_price) AS different_prices, SUM(gross_sales) AS gross_sales
FROM fact_sales WHERE is_sale = 1
GROUP BY product_id HAVING COUNT(*) >= 100 ORDER BY different_prices DESC LIMIT 30;

