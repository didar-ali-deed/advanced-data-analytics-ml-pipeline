# Business questions

Descriptive and diagnostic questions below are executed in stage 12. Generated answers supply numerical evidence, interpretation and potential action. Predictive and statistical questions follow.

## How complete and repetitive are accepted records?

Importance: Quantify confidence in downstream metrics.

Calculation: see the named `quality` query below.

```sql
SELECT COUNT(*) AS accepted_lines,
       SUM(CASE WHEN customer_id = 'UNKNOWN' THEN 1 ELSE 0 END) AS anonymous_lines,
       SUM(ambiguous_duplicate) AS ambiguous_repeat_lines,
       SUM(CASE WHEN unit_price = 0 THEN 1 ELSE 0 END) AS zero_price_lines
FROM fact_sales;
```

Output: `reports/exploratory/sql/quality.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Prioritize identifier capture and duplicate review.

## How much does ambiguous deduplication change gross sales?

Importance: Bound sensitivity to repeated business lines.

Calculation: see the named `duplicate_sensitivity` query below.

```sql
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
```

Output: `reports/exploratory/sql/duplicate_sensitivity.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Resolve source-line identity before deleting repeats.

## How much signed value comes from non-cancellation adjustments?

Importance: Separate inventory-like adjustments from sale performance.

Calculation: see the named `adjustments` query below.

```sql
SELECT SUM(is_adjustment) AS non_cancel_negative_lines,
       SUM(CASE WHEN is_adjustment THEN net_value ELSE 0 END) AS adjustment_value,
       SUM(CASE WHEN is_cancellation AND net_value > 0 THEN 1 ELSE 0 END)
           AS positive_cancellation_lines
FROM fact_sales;
```

Output: `reports/exploratory/sql/adjustments.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Review adjustment workflows with finance.

## What are total sales, cancellations, orders and known buyers?

Importance: Establish an executive baseline.

Calculation: see the named `overview` query below.

```sql
SELECT SUM(gross_sales) AS gross_sales, SUM(net_value) AS signed_value,
       SUM(cancellation_value) AS cancellation_value,
       COUNT(DISTINCT CASE WHEN is_sale THEN invoice_id END) AS sale_invoices,
       COUNT(DISTINCT CASE WHEN customer_id <> 'UNKNOWN' AND is_sale THEN customer_id END)
           AS known_buyers,
       SUM(gross_sales) / NULLIF(COUNT(DISTINCT CASE WHEN is_sale THEN invoice_id END), 0)
           AS average_invoice_gbp
FROM fact_sales;
```

Output: `reports/exploratory/sql/overview.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Use the defined KPI denominators consistently.

## How do recorded sales vary across months?

Importance: Support historical capacity planning.

Calculation: see the named `monthly` query below.

```sql
SELECT * FROM v_monthly ORDER BY month;
```

Output: `reports/exploratory/sql/monthly.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Compare complete periods before changing capacity.

## Which countries contribute the most gross sales?

Importance: Identify concentration and market exposure.

Calculation: see the named `country` query below.

```sql
SELECT c.country, SUM(f.gross_sales) AS gross_sales,
       COUNT(DISTINCT CASE WHEN f.is_sale THEN f.invoice_id END) AS orders,
       SUM(f.gross_sales) / SUM(SUM(f.gross_sales)) OVER () AS share
FROM fact_sales f JOIN dim_country c USING (country_id)
GROUP BY c.country ORDER BY gross_sales DESC;
```

Output: `reports/exploratory/sql/country.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Prioritize operational support for major markets.

## Which product codes lead gross sales and units?

Importance: Identify high-contribution assortment.

Calculation: see the named `products` query below.

```sql
SELECT p.product_id, p.description, SUM(f.gross_sales) AS gross_sales,
       SUM(CASE WHEN f.is_sale THEN f.quantity ELSE 0 END) AS sale_units,
       DENSE_RANK() OVER (ORDER BY SUM(f.gross_sales) DESC) AS revenue_rank
FROM fact_sales f JOIN dim_product p USING (product_id)
GROUP BY p.product_id, p.description ORDER BY gross_sales DESC LIMIT 30;
```

Output: `reports/exploratory/sql/products.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Review availability for leading codes; separate service codes.

## Where is cancellation value concentrated?

Importance: Find markets for cancellation review.

Calculation: see the named `cancellation_country` query below.

```sql
SELECT c.country, SUM(f.cancellation_value) AS cancellation_value,
       SUM(f.gross_sales) AS gross_sales,
       SUM(f.cancellation_value) / NULLIF(SUM(f.gross_sales), 0) AS value_ratio
FROM fact_sales f JOIN dim_country c USING (country_id)
GROUP BY c.country HAVING SUM(f.gross_sales) > 0 ORDER BY cancellation_value DESC;
```

Output: `reports/exploratory/sql/cancellation_country.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Investigate high-value exceptions without assuming return causes.

## What share of sales has no identified customer?

Importance: Assess bias in customer analytics.

Calculation: see the named `anonymous` query below.

```sql
SELECT CASE WHEN customer_id = 'UNKNOWN' THEN 'Anonymous' ELSE 'Identified' END AS segment,
       COUNT(*) AS lines, SUM(gross_sales) AS gross_sales,
       SUM(gross_sales) / SUM(SUM(gross_sales)) OVER () AS sales_share
FROM fact_sales GROUP BY segment;
```

Output: `reports/exploratory/sql/anonymous.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Improve identifier capture while retaining anonymous sales totals.

## How do average invoice sizes differ across countries?

Importance: Inform fulfillment capacity.

Calculation: see the named `baskets` query below.

```sql
SELECT c.country, COUNT(*) AS invoice_groups, AVG(i.gross_sales) AS average_invoice_gbp,
       AVG(i.sale_lines) AS average_lines, AVG(i.sale_units) AS average_units
FROM v_invoices i JOIN dim_country c USING (country_id)
WHERE i.gross_sales > 0 GROUP BY c.country ORDER BY invoice_groups DESC;
```

Output: `reports/exploratory/sql/baskets.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Review basket distributions and wholesale mix before intervention.

## Which weekdays have higher observed sales?

Importance: Plan recurring staffing patterns.

Calculation: see the named `weekday` query below.

```sql
SELECT weekday, COUNT(*) AS calendar_days, AVG(gross_sales) AS average_daily_sales,
       AVG(orders) AS average_orders FROM v_daily
GROUP BY weekday ORDER BY weekday;
```

Output: `reports/exploratory/sql/weekday.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Use calendar-day averages, including days with no records.

## When during source-local hours are sales recorded?

Importance: Describe intraday workload.

Calculation: see the named `hourly` query below.

```sql
SELECT hour, SUM(gross_sales) AS gross_sales, SUM(is_sale) AS sale_lines
FROM fact_sales GROUP BY hour ORDER BY hour;
```

Output: `reports/exploratory/sql/hourly.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Validate timezone and operating hours before scheduling changes.

## Which product codes show the most price variation?

Importance: Find pricing or metadata review candidates.

Calculation: see the named `prices` query below.

```sql
SELECT product_id, MIN(unit_price) AS min_price, MAX(unit_price) AS max_price,
       COUNT(DISTINCT unit_price) AS different_prices, SUM(gross_sales) AS gross_sales
FROM fact_sales WHERE is_sale = 1
GROUP BY product_id HAVING COUNT(*) >= 100 ORDER BY different_prices DESC LIMIT 30;
```

Output: `reports/exploratory/sql/prices.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Check discounts, descriptions and unit definitions.

## How do sales change month over month?

Importance: Track comparable-period momentum.

Calculation: see the named `growth` query below.

```sql
WITH lagged AS (
    SELECT *, LAG(gross_sales) OVER (ORDER BY month) AS previous_sales,
              LAG(complete_month) OVER (ORDER BY month) AS previous_complete
    FROM v_monthly
)
SELECT month, gross_sales, complete_month,
       CASE WHEN complete_month = 1 AND previous_complete = 1
            THEN gross_sales / NULLIF(previous_sales, 0) - 1 END AS mom_growth
FROM lagged ORDER BY month;
```

Output: `reports/exploratory/sql/growth.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Investigate large changes in complete months.

## How do complete months compare with the previous year?

Importance: Reduce seasonal confounding in growth review.

Calculation: see the named `yoy` query below.

```sql
SELECT current.month, current.gross_sales, prior.gross_sales AS previous_year_sales,
       current.gross_sales / NULLIF(prior.gross_sales, 0) - 1 AS yoy_growth
FROM v_monthly current JOIN v_monthly prior
  ON prior.month = STRFTIME('%Y-%m', DATE(current.month || '-01', '-1 year'))
WHERE current.complete_month = 1 AND prior.complete_month = 1 ORDER BY current.month;
```

Output: `reports/exploratory/sql/yoy.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Investigate product and customer mix behind changes.

## What do seven-day trends and running sales show?

Importance: Smooth daily operational volatility.

Calculation: see the named `rolling` query below.

```sql
SELECT date, gross_sales,
       AVG(gross_sales) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
           AS moving_7_day_sales,
       SUM(gross_sales) OVER (ORDER BY date) AS running_sales
FROM v_daily ORDER BY date;
```

Output: `reports/exploratory/sql/rolling.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Use trailing trends with the original daily series.

## How concentrated are known-customer sales?

Importance: Assess dependence on a few accounts.

Calculation: see the named `concentration` query below.

```sql
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
```

Output: `reports/exploratory/sql/concentration.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Monitor continuity for high-contribution customers.

## How much activity comes from repeat observed buyers?

Importance: Describe customer engagement within the observation window.

Calculation: see the named `repeat` query below.

```sql
WITH customers AS (
    SELECT customer_id, COUNT(DISTINCT invoice_id) AS orders, SUM(gross_sales) AS gross_sales
    FROM fact_sales WHERE customer_id <> 'UNKNOWN' AND is_sale = 1 GROUP BY customer_id
)
SELECT CASE WHEN orders = 1 THEN 'One observed invoice' ELSE 'Multiple observed invoices' END
           AS segment,
       COUNT(*) AS customers, SUM(gross_sales) AS gross_sales
FROM customers GROUP BY segment;
```

Output: `reports/exploratory/sql/repeat.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Design retention experiments; avoid lifetime claims.

## How often do customer cohorts buy again?

Importance: Compare observed retention patterns.

Calculation: see the named `cohorts` query below.

```sql
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
```

Output: `reports/exploratory/sql/cohorts.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Compare cohorts at equal maturity; flag incomplete last month.

## Which known customers have high recency, frequency and value?

Importance: Support a historical segmentation exercise.

Calculation: see the named `rfm` query below.

```sql
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
```

Output: `reports/exploratory/sql/rfm.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Validate outreach rules on contemporary consented data.

## Which dates have no recorded positive sales?

Importance: Expose calendar coverage assumptions.

Calculation: see the named `zero_days` query below.

```sql
SELECT date, weekday, recorded_lines, gross_sales FROM v_daily
WHERE gross_sales = 0 ORDER BY date;
```

Output: `reports/exploratory/sql/zero_days.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Confirm whether gaps reflect closure or missing capture.

## How concentrated are sales across product codes?

Importance: Identify assortment dependence.

Calculation: see the named `contributions` query below.

```sql
WITH c AS (
    SELECT p.product_id, p.description, SUM(f.gross_sales) AS gross_sales
    FROM fact_sales f JOIN dim_product p USING(product_id)
    GROUP BY p.product_id, p.description
)
SELECT *, gross_sales / SUM(gross_sales) OVER () AS sales_share,
       SUM(gross_sales) OVER (ORDER BY gross_sales DESC, product_id) / SUM(gross_sales) OVER ()
           AS cumulative_share
FROM c ORDER BY gross_sales DESC, product_id;
```

Output: `reports/exploratory/sql/contributions.csv`.

Interpretation: computed by stage 12 in [executed answers](../reports/business_insights/sql_answers.md); no result is assumed before execution.

Potential action: Review supply continuity for high-contribution codes.

## Can next-day recorded sales be predicted better than a seasonal baseline?

Importance: historical daily operations planning. Calculation: chronological holdout MAE/RMSE/R2/WAPE versus frozen mean and same-weekday baselines. Output: `models/evaluation/holdout_metrics.json`. Interpretation and action: generated by stage 23 from measured performance; validate on contemporary data before use.

## Do average customer basket values differ geographically?

Importance: diagnose customer mix. Calculation: Welch and Mann-Whitney contrasts, Holm adjustment and customer-level bootstrap. Output: `reports/statistical/statistics.json`. Interpretation: an observational association, not causal geography. Action: investigate mix and capture bias before intervention.
