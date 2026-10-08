# Executed business questions

## How complete and repetitive are accepted records?

**Importance:** Quantify confidence in downstream metrics.

**Calculation:**

```sql
SELECT COUNT(*) AS accepted_lines,
       SUM(CASE WHEN customer_id = 'UNKNOWN' THEN 1 ELSE 0 END) AS anonymous_lines,
       SUM(ambiguous_duplicate) AS ambiguous_repeat_lines,
       SUM(CASE WHEN unit_price = 0 THEN 1 ELSE 0 END) AS zero_price_lines
FROM fact_sales;
```

|   accepted_lines |   anonymous_lines |   ambiguous_repeat_lines |   zero_price_lines |
|-----------------:|------------------:|-------------------------:|-------------------:|
|      1.04484e+06 |            235282 |                    22813 |               6024 |

**Output:** [quality](../../reports/exploratory/sql/quality.csv)

**Interpretation:** Output contains 1 groups/periods. First reported result: accepted_lines=1.045e+06; anonymous_lines=2.353e+05; ambiguous_repeat_lines=2.281e+04; zero_price_lines=6,024.

**Potential action:** Prioritize identifier capture and duplicate review.

## How much does ambiguous deduplication change gross sales?

**Importance:** Bound sensitivity to repeated business lines.

**Calculation:**

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

|   retained_gross_sales |   hypothetical_deduplicated_sales |   ambiguous_value_difference |
|-----------------------:|----------------------------------:|-----------------------------:|
|            2.05337e+07 |                       2.04757e+07 |                      58033.3 |

**Output:** [duplicate_sensitivity](../../reports/exploratory/sql/duplicate_sensitivity.csv)

**Interpretation:** Hypothetical removal of repeated business rows changes gross sales by GBP 58,033.32; identity remains uncertain.

**Potential action:** Resolve source-line identity before deleting repeats.

## How much signed value comes from non-cancellation adjustments?

**Importance:** Separate inventory-like adjustments from sale performance.

**Calculation:**

```sql
SELECT SUM(is_adjustment) AS non_cancel_negative_lines,
       SUM(CASE WHEN is_adjustment THEN net_value ELSE 0 END) AS adjustment_value,
       SUM(CASE WHEN is_cancellation AND net_value > 0 THEN 1 ELSE 0 END)
           AS positive_cancellation_lines
FROM fact_sales;
```

|   non_cancel_negative_lines |   adjustment_value |   positive_cancellation_lines |
|----------------------------:|-------------------:|------------------------------:|
|                        3393 |                  0 |                             1 |

**Output:** [adjustments](../../reports/exploratory/sql/adjustments.csv)

**Interpretation:** Output contains 1 groups/periods. First reported result: non_cancel_negative_lines=3,393; adjustment_value=0; positive_cancellation_lines=1.

**Potential action:** Review adjustment workflows with finance.

## What are total sales, cancellations, orders and known buyers?

**Importance:** Establish an executive baseline.

**Calculation:**

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

|   gross_sales |   signed_value |   cancellation_value |   sale_invoices |   known_buyers |   average_invoice_gbp |
|--------------:|---------------:|---------------------:|----------------:|---------------:|----------------------:|
|   2.05337e+07 |    1.90684e+07 |          1.46568e+06 |           40077 |           5878 |               512.357 |

**Output:** [overview](../../reports/exploratory/sql/overview.csv)

**Interpretation:** Gross sales were GBP 20,533,741.92; cancellation value was GBP 1,465,677.23; 40,077 sale invoices were observed.

**Potential action:** Use the defined KPI denominators consistently.

## How do recorded sales vary across months?

**Importance:** Support historical capacity planning.

**Calculation:**

```sql
SELECT * FROM v_monthly ORDER BY month;
```

| month   |   gross_sales |   net_value |   cancellation_value |   orders |   complete_month |
|:--------|--------------:|------------:|---------------------:|---------:|-----------------:|
| 2009-12 |        825686 |      799847 |              25838.7 |     1682 |                1 |
| 2010-01 |        652709 |      624033 |              28675.6 |     1105 |                1 |
| 2010-02 |        553340 |      533091 |              20621.9 |     1201 |                1 |
| 2010-03 |        833570 |      765849 |              67721.4 |     1681 |                1 |
| 2010-04 |        681529 |      644175 |              37354.2 |     1462 |                1 |

**Output:** [monthly](../../reports/exploratory/sql/monthly.csv)

**Interpretation:** Output contains 25 groups/periods. First reported result: month=2009-12; gross_sales=8.257e+05; net_value=7.998e+05; cancellation_value=2.584e+04; orders=1,682; complete_month=1.

**Potential action:** Compare complete periods before changing capacity.

## Which countries contribute the most gross sales?

**Importance:** Identify concentration and market exposure.

**Calculation:**

```sql
SELECT c.country, SUM(f.gross_sales) AS gross_sales,
       COUNT(DISTINCT CASE WHEN f.is_sale THEN f.invoice_id END) AS orders,
       SUM(f.gross_sales) / SUM(SUM(f.gross_sales)) OVER () AS share
FROM fact_sales f JOIN dim_country c USING (country_id)
GROUP BY c.country ORDER BY gross_sales DESC;
```

| country        |      gross_sales |   orders |     share |
|:---------------|-----------------:|---------:|----------:|
| United Kingdom |      1.74659e+07 |    36535 | 0.850595  |
| EIRE           | 659149           |      626 | 0.0321008 |
| Netherlands    | 554040           |      228 | 0.0269819 |
| Germany        | 425578           |      789 | 0.0207258 |
| France         | 350654           |      622 | 0.017077  |

**Output:** [country](../../reports/exploratory/sql/country.csv)

**Interpretation:** United Kingdom led with 85.1% of accepted gross sales.

**Potential action:** Prioritize operational support for major markets.

## Which product codes lead gross sales and units?

**Importance:** Identify high-contribution assortment.

**Calculation:**

```sql
SELECT p.product_id, p.description, SUM(f.gross_sales) AS gross_sales,
       SUM(CASE WHEN f.is_sale THEN f.quantity ELSE 0 END) AS sale_units,
       DENSE_RANK() OVER (ORDER BY SUM(f.gross_sales) DESC) AS revenue_rank
FROM fact_sales f JOIN dim_product p USING (product_id)
GROUP BY p.product_id, p.description ORDER BY gross_sales DESC LIMIT 30;
```

| product_id   | description                        |   gross_sales |   sale_units |   revenue_rank |
|:-------------|:-----------------------------------|--------------:|-------------:|---------------:|
| M            | Manual                             |        339615 |         9931 |              1 |
| 22423        | REGENCY CAKESTAND 3 TIER           |        331084 |        26519 |              2 |
| DOT          | DOTCOM POSTAGE                     |        309854 |         1415 |              3 |
| 85123A       | CREAM HANGING HEART T-LIGHT HOLDER |        258066 |        94323 |              4 |
| 85099B       | JUMBO BAG RED RETROSPOT            |        180888 |        96931 |              5 |

**Output:** [products](../../reports/exploratory/sql/products.csv)

**Interpretation:** Output contains 30 groups/periods. First reported result: product_id=M; description=Manual; gross_sales=3.396e+05; sale_units=9,931; revenue_rank=1.

**Potential action:** Review availability for leading codes; separate service codes.

## Where is cancellation value concentrated?

**Importance:** Find markets for cancellation review.

**Calculation:**

```sql
SELECT c.country, SUM(f.cancellation_value) AS cancellation_value,
       SUM(f.gross_sales) AS gross_sales,
       SUM(f.cancellation_value) / NULLIF(SUM(f.gross_sales), 0) AS value_ratio
FROM fact_sales f JOIN dim_country c USING (country_id)
GROUP BY c.country HAVING SUM(f.gross_sales) > 0 ORDER BY cancellation_value DESC;
```

| country        |   cancellation_value |      gross_sales |   value_ratio |
|:---------------|---------------------:|-----------------:|--------------:|
| United Kingdom |          1.26899e+06 |      1.74659e+07 |     0.0726554 |
| EIRE           |      48904.7         | 659149           |     0.0741937 |
| France         |      28725.7         | 350654           |     0.0819202 |
| Norway         |      20866.6         |  56322.5         |     0.370484  |
| Spain          |      17319           | 108384           |     0.159794  |

**Output:** [cancellation_country](../../reports/exploratory/sql/cancellation_country.csv)

**Interpretation:** Output contains 43 groups/periods. First reported result: country=United Kingdom; cancellation_value=1.269e+06; gross_sales=1.747e+07; value_ratio=0.07266.

**Potential action:** Investigate high-value exceptions without assuming return causes.

## What share of sales has no identified customer?

**Importance:** Assess bias in customer analytics.

**Calculation:**

```sql
SELECT CASE WHEN customer_id = 'UNKNOWN' THEN 'Anonymous' ELSE 'Identified' END AS segment,
       COUNT(*) AS lines, SUM(gross_sales) AS gross_sales,
       SUM(gross_sales) / SUM(SUM(gross_sales)) OVER () AS sales_share
FROM fact_sales GROUP BY segment;
```

| segment    |   lines |   gross_sales |   sales_share |
|:-----------|--------:|--------------:|--------------:|
| Anonymous  |  235282 |   3.10219e+06 |      0.151078 |
| Identified |  809561 |   1.74316e+07 |      0.848922 |

**Output:** [anonymous](../../reports/exploratory/sql/anonymous.csv)

**Interpretation:** Output contains 2 groups/periods. First reported result: segment=Anonymous; lines=2.353e+05; gross_sales=3.102e+06; sales_share=0.1511.

**Potential action:** Improve identifier capture while retaining anonymous sales totals.

## How do average invoice sizes differ across countries?

**Importance:** Inform fulfillment capacity.

**Calculation:**

```sql
SELECT c.country, COUNT(*) AS invoice_groups, AVG(i.gross_sales) AS average_invoice_gbp,
       AVG(i.sale_lines) AS average_lines, AVG(i.sale_units) AS average_units
FROM v_invoices i JOIN dim_country c USING (country_id)
WHERE i.gross_sales > 0 GROUP BY c.country ORDER BY invoice_groups DESC;
```

| country        |   invoice_groups |   average_invoice_gbp |   average_lines |   average_units |
|:---------------|-----------------:|----------------------:|----------------:|----------------:|
| United Kingdom |            36535 |               478.059 |         25.6639 |         252.39  |
| Germany        |              789 |               539.39  |         20.8568 |         285.638 |
| EIRE           |              626 |              1052.95  |         27.4345 |         537.642 |
| France         |              622 |               563.753 |         21.9807 |         437.457 |
| Netherlands    |              228 |              2430     |         22.307  |        1683.68  |

**Output:** [baskets](../../reports/exploratory/sql/baskets.csv)

**Interpretation:** Output contains 43 groups/periods. First reported result: country=United Kingdom; invoice_groups=3.654e+04; average_invoice_gbp=478.1; average_lines=25.66; average_units=252.4.

**Potential action:** Review basket distributions and wholesale mix before intervention.

## Which weekdays have higher observed sales?

**Importance:** Plan recurring staffing patterns.

**Calculation:**

```sql
SELECT weekday, COUNT(*) AS calendar_days, AVG(gross_sales) AS average_daily_sales,
       AVG(orders) AS average_orders FROM v_daily
GROUP BY weekday ORDER BY weekday;
```

|   weekday |   calendar_days |   average_daily_sales |   average_orders |
|----------:|----------------:|----------------------:|-----------------:|
|         0 |             105 |               34189.8 |          60.4857 |
|         1 |             106 |               38549.5 |          68.783  |
|         2 |             106 |               32994.7 |          67.783  |
|         3 |             106 |               39670.4 |          78.1887 |
|         4 |             106 |               31415.4 |          57.5189 |

**Output:** [weekday](../../reports/exploratory/sql/weekday.csv)

**Interpretation:** Output contains 7 groups/periods. First reported result: weekday=0; calendar_days=105; average_daily_sales=3.419e+04; average_orders=60.49.

**Potential action:** Use calendar-day averages, including days with no records.

## When during source-local hours are sales recorded?

**Importance:** Describe intraday workload.

**Calculation:**

```sql
SELECT hour, SUM(gross_sales) AS gross_sales, SUM(is_sale) AS sale_lines
FROM fact_sales GROUP BY hour ORDER BY hour;
```

|   hour |      gross_sales |   sale_lines |
|-------:|-----------------:|-------------:|
|      6 |      4.25        |            1 |
|      7 |  75765.6         |         1054 |
|      8 | 528319           |        15530 |
|      9 |      1.76996e+06 |        65874 |
|     10 |      2.58486e+06 |        88742 |

**Output:** [hourly](../../reports/exploratory/sql/hourly.csv)

**Interpretation:** Output contains 16 groups/periods. First reported result: hour=6; gross_sales=4.25; sale_lines=1.

**Potential action:** Validate timezone and operating hours before scheduling changes.

## Which product codes show the most price variation?

**Importance:** Find pricing or metadata review candidates.

**Calculation:**

```sql
SELECT product_id, MIN(unit_price) AS min_price, MAX(unit_price) AS max_price,
       COUNT(DISTINCT unit_price) AS different_prices, SUM(gross_sales) AS gross_sales
FROM fact_sales WHERE is_sale = 1
GROUP BY product_id HAVING COUNT(*) >= 100 ORDER BY different_prices DESC LIMIT 30;
```

| product_id   |   min_price |   max_price |   different_prices |   gross_sales |
|:-------------|------------:|------------:|-------------------:|--------------:|
| DOT          |        0.35 |     4505.17 |               1290 |      309854   |
| M            |        0.06 |    25111.1  |                298 |      339615   |
| POST         |        0.5  |     8142.75 |                 81 |      125682   |
| 20685        |        4    |       16.98 |                 21 |       66464.7 |
| 21033        |        1.25 |        6.04 |                 18 |       10157.8 |

**Output:** [prices](../../reports/exploratory/sql/prices.csv)

**Interpretation:** Output contains 30 groups/periods. First reported result: product_id=DOT; min_price=0.35; max_price=4,505; different_prices=1,290; gross_sales=3.099e+05.

**Potential action:** Check discounts, descriptions and unit definitions.

## How do sales change month over month?

**Importance:** Track comparable-period momentum.

**Calculation:**

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

| month   |   gross_sales |   complete_month |   mom_growth |
|:--------|--------------:|-----------------:|-------------:|
| 2009-12 |        825686 |                1 |   nan        |
| 2010-01 |        652709 |                1 |    -0.209495 |
| 2010-02 |        553340 |                1 |    -0.152241 |
| 2010-03 |        833570 |                1 |     0.506435 |
| 2010-04 |        681529 |                1 |    -0.182398 |

**Output:** [growth](../../reports/exploratory/sql/growth.csv)

**Interpretation:** Output contains 25 groups/periods. First reported result: month=2009-12; gross_sales=8.257e+05; complete_month=1; mom_growth=nan.

**Potential action:** Investigate large changes in complete months.

## How do complete months compare with the previous year?

**Importance:** Reduce seasonal confounding in growth review.

**Calculation:**

```sql
SELECT current.month, current.gross_sales, prior.gross_sales AS previous_year_sales,
       current.gross_sales / NULLIF(prior.gross_sales, 0) - 1 AS yoy_growth
FROM v_monthly current JOIN v_monthly prior
  ON prior.month = STRFTIME('%Y-%m', DATE(current.month || '-01', '-1 year'))
WHERE current.complete_month = 1 AND prior.complete_month = 1 ORDER BY current.month;
```

| month   |   gross_sales |   previous_year_sales |   yoy_growth |
|:--------|--------------:|----------------------:|-------------:|
| 2010-12 |        823746 |                825686 |   -0.0023491 |
| 2011-01 |        691365 |                652709 |    0.0592241 |
| 2011-02 |        523632 |                553340 |   -0.0536883 |
| 2011-03 |        717639 |                833570 |   -0.139077  |
| 2011-04 |        537809 |                681529 |   -0.210879  |

**Output:** [yoy](../../reports/exploratory/sql/yoy.csv)

**Interpretation:** Output contains 12 groups/periods. First reported result: month=2010-12; gross_sales=8.237e+05; previous_year_sales=8.257e+05; yoy_growth=-0.002349.

**Potential action:** Investigate product and customer mix behind changes.

## What do seven-day trends and running sales show?

**Importance:** Smooth daily operational volatility.

**Calculation:**

```sql
SELECT date, gross_sales,
       AVG(gross_sales) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
           AS moving_7_day_sales,
       SUM(gross_sales) OVER (ORDER BY date) AS running_sales
FROM v_daily ORDER BY date;
```

| date       |   gross_sales |   moving_7_day_sales |   running_sales |
|:-----------|--------------:|---------------------:|----------------:|
| 2009-12-01 |      54513.5  |              54513.5 |         54513.5 |
| 2009-12-02 |      63352.5  |              58933   |        117866   |
| 2009-12-03 |      74037.9  |              63968   |        191904   |
| 2009-12-04 |      40732.9  |              58159.2 |        232637   |
| 2009-12-05 |       9803.05 |              48488   |        242440   |

**Output:** [rolling](../../reports/exploratory/sql/rolling.csv)

**Interpretation:** Output contains 739 groups/periods. First reported result: date=2009-12-01; gross_sales=5.451e+04; moving_7_day_sales=5.451e+04; running_sales=5.451e+04.

**Potential action:** Use trailing trends with the original daily series.

## How concentrated are known-customer sales?

**Importance:** Assess dependence on a few accounts.

**Calculation:**

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

|   rank |   customer_id |   gross_sales |     share |   cumulative_share |
|-------:|--------------:|--------------:|----------:|-------------------:|
|      1 |         18102 |        580987 | 0.0333296 |          0.0333296 |
|      2 |         14646 |        528603 | 0.0303245 |          0.0636541 |
|      3 |         14156 |        313624 | 0.0179918 |          0.0816458 |
|      4 |         14911 |        291561 | 0.0167261 |          0.0983719 |
|      5 |         17450 |        244944 | 0.0140518 |          0.112424  |

**Output:** [concentration](../../reports/exploratory/sql/concentration.csv)

**Interpretation:** Output contains 100 groups/periods. First reported result: rank=1; customer_id=18102; gross_sales=5.81e+05; share=0.03333; cumulative_share=0.03333.

**Potential action:** Monitor continuity for high-contribution customers.

## How much activity comes from repeat observed buyers?

**Importance:** Describe customer engagement within the observation window.

**Calculation:**

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

| segment                    |   customers |      gross_sales |
|:---------------------------|------------:|-----------------:|
| Multiple observed invoices |        4255 |      1.68688e+07 |
| One observed invoice       |        1623 | 562795           |

**Output:** [repeat](../../reports/exploratory/sql/repeat.csv)

**Interpretation:** Output contains 2 groups/periods. First reported result: segment=Multiple observed invoices; customers=4,255; gross_sales=1.687e+07.

**Potential action:** Design retention experiments; avoid lifetime claims.

## How often do customer cohorts buy again?

**Importance:** Compare observed retention patterns.

**Calculation:**

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

| cohort   | month   |   months_since_first |   active_customers |   initial_customers |   observed_retention |
|:---------|:--------|---------------------:|-------------------:|--------------------:|---------------------:|
| 2009-12  | 2009-12 |                    0 |                955 |                 955 |             1        |
| 2009-12  | 2010-01 |                    1 |                337 |                 955 |             0.35288  |
| 2009-12  | 2010-02 |                    2 |                319 |                 955 |             0.334031 |
| 2009-12  | 2010-03 |                    3 |                406 |                 955 |             0.425131 |
| 2009-12  | 2010-04 |                    4 |                363 |                 955 |             0.380105 |

**Output:** [cohorts](../../reports/exploratory/sql/cohorts.csv)

**Interpretation:** 25 observed first-purchase cohorts span 325 cohort-month cells. Later cohorts have shorter follow-up; absent future cells are unobserved, not zero retention.

**Potential action:** Compare cohorts at equal maturity; flag incomplete last month.

## Which known customers have high recency, frequency and value?

**Importance:** Support a historical segmentation exercise.

**Calculation:**

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

|   customer_id |   recency_days |   frequency |   monetary |   monetary_quartile |
|--------------:|---------------:|------------:|-----------:|--------------------:|
|         18102 |              0 |         145 |     580987 |                   4 |
|         14646 |              1 |         151 |     528603 |                   4 |
|         14156 |              9 |         156 |     313624 |                   4 |
|         14911 |              1 |         398 |     291561 |                   4 |
|         17450 |              8 |          51 |     244944 |                   4 |

**Output:** [rfm](../../reports/exploratory/sql/rfm.csv)

**Interpretation:** Output contains 5,878 groups/periods. First reported result: customer_id=18102; recency_days=0; frequency=145; monetary=5.81e+05; monetary_quartile=4.

**Potential action:** Validate outreach rules on contemporary consented data.

## Which dates have no recorded positive sales?

**Importance:** Expose calendar coverage assumptions.

**Calculation:**

```sql
SELECT date, weekday, recorded_lines, gross_sales FROM v_daily
WHERE gross_sales = 0 ORDER BY date;
```

| date       |   weekday |   recorded_lines |   gross_sales |
|:-----------|----------:|-----------------:|--------------:|
| 2009-12-12 |         5 |                0 |             0 |
| 2009-12-19 |         5 |                0 |             0 |
| 2009-12-24 |         3 |                0 |             0 |
| 2009-12-25 |         4 |                0 |             0 |
| 2009-12-26 |         5 |                0 |             0 |

**Output:** [zero_days](../../reports/exploratory/sql/zero_days.csv)

**Interpretation:** 135 calendar days had no positive recorded sales; the cause is unobserved.

**Potential action:** Confirm whether gaps reflect closure or missing capture.

## How concentrated are sales across product codes?

**Importance:** Identify assortment dependence.

**Calculation:**

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

| product_id   | description                        |   gross_sales |   sales_share |   cumulative_share |
|:-------------|:-----------------------------------|--------------:|--------------:|-------------------:|
| M            | Manual                             |        339615 |    0.0165394  |          0.0165394 |
| 22423        | REGENCY CAKESTAND 3 TIER           |        331084 |    0.0161239  |          0.0326633 |
| DOT          | DOTCOM POSTAGE                     |        309854 |    0.01509    |          0.0477533 |
| 85123A       | CREAM HANGING HEART T-LIGHT HOLDER |        258066 |    0.0125679  |          0.0603212 |
| 85099B       | JUMBO BAG RED RETROSPOT            |        180888 |    0.00880931 |          0.0691305 |

**Output:** [contributions](../../reports/exploratory/sql/contributions.csv)

**Interpretation:** Output contains 5,304 groups/periods. First reported result: product_id=M; description=Manual; gross_sales=3.396e+05; sales_share=0.01654; cumulative_share=0.01654.

**Potential action:** Review supply continuity for high-contribution codes.

