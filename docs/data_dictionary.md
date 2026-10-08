# Data dictionary

Amounts remain GBP; timestamps preserve source-local naive values. Identifiers are strings.

| Source | Standardized | Meaning / rule |
|---|---|---|
| Invoice | invoice_id | Invoice identifier; C prefix denotes cancellation. Repeats across line items are valid. |
| StockCode | product_id | Product/service code; retain alphanumeric codes and leading zeros. |
| Description | description | Item description; missing → UNKNOWN; whitespace normalized. |
| Quantity | quantity | Signed integral quantity; negative values retained as cancellations/adjustments. |
| InvoiceDate | invoice_date | Recorded timestamp; invalid/out-of-coverage values quarantined. |
| Price | unit_price | GBP per unit; negative/nonfinite prices quarantined; zero prices retained. |
| Customer ID | customer_id | Customer identifier; missing → UNKNOWN, never inferred. |
| Country | country | Recorded transaction country; no undocumented harmonization. |
| Derived lineage | line_id | Source sheet name plus original Excel row number, e.g. Year 2009-2010:2. |
| Derived lineage | source_sheet/source_row | Raw record provenance; retained in intermediate/cleaned tables. |
| Derived | is_sale | Positive quantity and price and not C-prefixed. |
| Derived | is_cancellation | C-prefixed invoice, case insensitive. |
| Derived | is_adjustment | Negative quantity outside C-prefixed invoices. |
| Derived | ambiguous_duplicate | Repeated normalized business rows retained after cross-sheet reconciliation. |
| Derived | net_value | Signed quantity × unit price, not profit or audited net revenue. |
| Derived | gross_sales | net_value for is_sale rows, zero otherwise. |
| Derived | cancellation_value | Absolute negative signed value for cancellation lines, zero otherwise. |

**Grains:** fact_sales is accepted source line; dim_product is code with latest observed description; dim_customer is identifier only; dim_country is observed country with deterministic integer key; dim_date is each calendar date in the source coverage. v_invoices groups invoice/customer/country; one invoice ID may appear in multiple groups.

**Daily model target:** total recorded gross_sales on day t. Numerical calendar features describe t; lag_1/7/14/28 and lag_orders_1 reference earlier dates; rolling_7/28 and rolling_std_7 use shifted sales through t−1. trend_7_28 divides those lagged means and is missing when the denominator is zero. Annual sine/cosine use day of year. The first 28 days are warm-up; the final possibly partial source date is excluded from labeled examples.

Stage 24 produces `data/powerbi/data_dictionary.csv` with every exported column, dtype and null count. Calendar flags and numerical units must match the Power BI instructions.

