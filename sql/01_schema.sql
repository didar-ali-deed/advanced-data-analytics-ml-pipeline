PRAGMA foreign_keys = ON;
CREATE TABLE dim_product (product_id TEXT PRIMARY KEY, description TEXT NOT NULL);
CREATE TABLE dim_customer (customer_id TEXT PRIMARY KEY);
CREATE TABLE dim_country (country TEXT NOT NULL UNIQUE, country_id INTEGER PRIMARY KEY);
CREATE TABLE dim_date (
    date TEXT PRIMARY KEY, year INTEGER NOT NULL, month_number INTEGER NOT NULL,
    weekday INTEGER NOT NULL CHECK(weekday BETWEEN 0 AND 6)
);
CREATE TABLE fact_sales (
    line_id TEXT PRIMARY KEY, invoice_id TEXT NOT NULL,
    product_id TEXT NOT NULL REFERENCES dim_product(product_id),
    customer_id TEXT NOT NULL REFERENCES dim_customer(customer_id),
    country_id INTEGER NOT NULL REFERENCES dim_country(country_id),
    date TEXT NOT NULL REFERENCES dim_date(date), invoice_date TEXT NOT NULL,
    quantity INTEGER NOT NULL, unit_price REAL NOT NULL CHECK(unit_price >= 0),
    net_value REAL NOT NULL, gross_sales REAL NOT NULL CHECK(gross_sales >= 0),
    cancellation_value REAL NOT NULL CHECK(cancellation_value >= 0),
    is_sale INTEGER NOT NULL CHECK(is_sale IN (0, 1)),
    is_cancellation INTEGER NOT NULL CHECK(is_cancellation IN (0, 1)),
    is_adjustment INTEGER NOT NULL CHECK(is_adjustment IN (0, 1)),
    ambiguous_duplicate INTEGER NOT NULL CHECK(ambiguous_duplicate IN (0, 1)),
    hour INTEGER NOT NULL CHECK(hour BETWEEN 0 AND 23)
);
CREATE INDEX idx_sales_date ON fact_sales(date);
CREATE INDEX idx_sales_customer ON fact_sales(customer_id);
CREATE INDEX idx_sales_product ON fact_sales(product_id);
CREATE INDEX idx_sales_invoice ON fact_sales(invoice_id);
CREATE INDEX idx_sales_country ON fact_sales(country_id);

