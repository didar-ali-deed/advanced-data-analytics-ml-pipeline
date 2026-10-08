CREATE VIEW v_daily AS
SELECT d.date, d.weekday,
    COALESCE(SUM(f.gross_sales), 0) AS gross_sales,
    COALESCE(SUM(f.net_value), 0) AS net_value,
    COALESCE(SUM(f.cancellation_value), 0) AS cancellation_value,
    COUNT(DISTINCT CASE WHEN f.is_sale = 1 THEN f.invoice_id END) AS orders,
    COUNT(f.line_id) AS recorded_lines
FROM dim_date d LEFT JOIN fact_sales f ON d.date = f.date
GROUP BY d.date, d.weekday;

CREATE VIEW v_monthly AS
SELECT SUBSTR(date, 1, 7) AS month, SUM(gross_sales) AS gross_sales,
    SUM(net_value) AS net_value, SUM(cancellation_value) AS cancellation_value,
    SUM(orders) AS orders,
    CASE WHEN MIN(date) = DATE(MIN(date), 'start of month')
         AND MAX(date) = DATE(MAX(date), 'start of month', '+1 month', '-1 day')
         THEN 1 ELSE 0 END AS complete_month
FROM v_daily GROUP BY SUBSTR(date, 1, 7);

CREATE VIEW v_invoices AS
SELECT invoice_id, customer_id, country_id, MIN(date) AS date,
    SUM(gross_sales) AS gross_sales, SUM(cancellation_value) AS cancellation_value,
    SUM(is_sale) AS sale_lines, SUM(CASE WHEN is_sale THEN quantity ELSE 0 END) AS sale_units
FROM fact_sales GROUP BY invoice_id, customer_id, country_id;

