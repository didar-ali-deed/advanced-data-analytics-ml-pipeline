# UCI Retail Observatory: final analytical report

## Executive summary

Gross sales were GBP 20,533,741.92; cancellation value was GBP 1,465,677.23; 40,077 sale invoices were observed. United Kingdom led with 85.1% of accepted gross sales.

Validated 1,067,371 source lines; retained 1,044,843; quarantined 22,528. Selected forecast model: **ridge**.

## Sources and dataset

[Online Retail II](https://archive.ics.uci.edu/dataset/502/online%2Bretail%2Bii), Daqing Chen, UCI Machine Learning Repository; CC BY 4.0; DOI 10.24432/C5CG6D. Retrieved 2026-10-08T03:56:05.907530+00:00. Archive SHA-256: `572e36277c2390fbfde10664750731e0a86f55e33470d91919085f0408e67bfb`. Original Excel sheets are preserved. Dimensions are derived from this single source.

## Business objectives

Describe sales and cancellation exposure, diagnose geographic/product/customer concentration, quantify data-quality sensitivity, and evaluate next-day recorded-sales prediction. The project answers 22 SQL business questions plus statistical and predictive questions.

## Data quality and cleaning

|                                   |          records |
|:----------------------------------|-----------------:|
| original_rows                     |      1.06737e+06 |
| accepted_rows                     |      1.04484e+06 |
| quarantined_rows                  |  22528           |
| unknown_customers                 | 235282           |
| ambiguous_duplicate_rows_retained |  22813           |

Impossible values are quarantined with reasons. Negative quantities and cancellations remain. Exact cross-sheet overlap copies are quarantined using original-field equality and per-sheet multiplicity. Ambiguous within-sheet repeated lines remain; sensitivity is separately reported. Missing customer IDs are UNKNOWN, never fabricated. Raw files remain immutable.

## Analytical methodology and relational reconciliation

Gross sales use positive quantity and price outside cancellation invoices; signed value includes adjustments and is not profit. All amounts remain GBP. Dates retain undocumented source-local timezone semantics. Calendar gaps mean zero observed sales, not known closure. Integrated 1,044,843 fact rows with 0 orphans. SQLite enforces primary/foreign keys; SQL uses windows, CTEs and comparable-period filters.

## SQL findings

### How complete and repetitive are accepted records?

Output contains 1 groups/periods. First reported result: accepted_lines=1.045e+06; anonymous_lines=2.353e+05; ambiguous_repeat_lines=2.281e+04; zero_price_lines=6,024.

Action to evaluate: Prioritize identifier capture and duplicate review. [Complete result](../../reports/exploratory/sql/quality.csv).

### How much does ambiguous deduplication change gross sales?

Hypothetical removal of repeated business rows changes gross sales by GBP 58,033.32; identity remains uncertain.

Action to evaluate: Resolve source-line identity before deleting repeats. [Complete result](../../reports/exploratory/sql/duplicate_sensitivity.csv).

### How much signed value comes from non-cancellation adjustments?

Output contains 1 groups/periods. First reported result: non_cancel_negative_lines=3,393; adjustment_value=0; positive_cancellation_lines=1.

Action to evaluate: Review adjustment workflows with finance. [Complete result](../../reports/exploratory/sql/adjustments.csv).

### What are total sales, cancellations, orders and known buyers?

Gross sales were GBP 20,533,741.92; cancellation value was GBP 1,465,677.23; 40,077 sale invoices were observed.

Action to evaluate: Use the defined KPI denominators consistently. [Complete result](../../reports/exploratory/sql/overview.csv).

### How do recorded sales vary across months?

Output contains 25 groups/periods. First reported result: month=2009-12; gross_sales=8.257e+05; net_value=7.998e+05; cancellation_value=2.584e+04; orders=1,682; complete_month=1.

Action to evaluate: Compare complete periods before changing capacity. [Complete result](../../reports/exploratory/sql/monthly.csv).

### Which countries contribute the most gross sales?

United Kingdom led with 85.1% of accepted gross sales.

Action to evaluate: Prioritize operational support for major markets. [Complete result](../../reports/exploratory/sql/country.csv).

### Which product codes lead gross sales and units?

Output contains 30 groups/periods. First reported result: product_id=M; description=Manual; gross_sales=3.396e+05; sale_units=9,931; revenue_rank=1.

Action to evaluate: Review availability for leading codes; separate service codes. [Complete result](../../reports/exploratory/sql/products.csv).

### Where is cancellation value concentrated?

Output contains 43 groups/periods. First reported result: country=United Kingdom; cancellation_value=1.269e+06; gross_sales=1.747e+07; value_ratio=0.07266.

Action to evaluate: Investigate high-value exceptions without assuming return causes. [Complete result](../../reports/exploratory/sql/cancellation_country.csv).

### What share of sales has no identified customer?

Output contains 2 groups/periods. First reported result: segment=Anonymous; lines=2.353e+05; gross_sales=3.102e+06; sales_share=0.1511.

Action to evaluate: Improve identifier capture while retaining anonymous sales totals. [Complete result](../../reports/exploratory/sql/anonymous.csv).

### How do average invoice sizes differ across countries?

Output contains 43 groups/periods. First reported result: country=United Kingdom; invoice_groups=3.654e+04; average_invoice_gbp=478.1; average_lines=25.66; average_units=252.4.

Action to evaluate: Review basket distributions and wholesale mix before intervention. [Complete result](../../reports/exploratory/sql/baskets.csv).

### Which weekdays have higher observed sales?

Output contains 7 groups/periods. First reported result: weekday=0; calendar_days=105; average_daily_sales=3.419e+04; average_orders=60.49.

Action to evaluate: Use calendar-day averages, including days with no records. [Complete result](../../reports/exploratory/sql/weekday.csv).

### When during source-local hours are sales recorded?

Output contains 16 groups/periods. First reported result: hour=6; gross_sales=4.25; sale_lines=1.

Action to evaluate: Validate timezone and operating hours before scheduling changes. [Complete result](../../reports/exploratory/sql/hourly.csv).

### Which product codes show the most price variation?

Output contains 30 groups/periods. First reported result: product_id=DOT; min_price=0.35; max_price=4,505; different_prices=1,290; gross_sales=3.099e+05.

Action to evaluate: Check discounts, descriptions and unit definitions. [Complete result](../../reports/exploratory/sql/prices.csv).

### How do sales change month over month?

Output contains 25 groups/periods. First reported result: month=2009-12; gross_sales=8.257e+05; complete_month=1; mom_growth=nan.

Action to evaluate: Investigate large changes in complete months. [Complete result](../../reports/exploratory/sql/growth.csv).

### How do complete months compare with the previous year?

Output contains 12 groups/periods. First reported result: month=2010-12; gross_sales=8.237e+05; previous_year_sales=8.257e+05; yoy_growth=-0.002349.

Action to evaluate: Investigate product and customer mix behind changes. [Complete result](../../reports/exploratory/sql/yoy.csv).

### What do seven-day trends and running sales show?

Output contains 739 groups/periods. First reported result: date=2009-12-01; gross_sales=5.451e+04; moving_7_day_sales=5.451e+04; running_sales=5.451e+04.

Action to evaluate: Use trailing trends with the original daily series. [Complete result](../../reports/exploratory/sql/rolling.csv).

### How concentrated are known-customer sales?

Output contains 100 groups/periods. First reported result: rank=1; customer_id=18102; gross_sales=5.81e+05; share=0.03333; cumulative_share=0.03333.

Action to evaluate: Monitor continuity for high-contribution customers. [Complete result](../../reports/exploratory/sql/concentration.csv).

### How much activity comes from repeat observed buyers?

Output contains 2 groups/periods. First reported result: segment=Multiple observed invoices; customers=4,255; gross_sales=1.687e+07.

Action to evaluate: Design retention experiments; avoid lifetime claims. [Complete result](../../reports/exploratory/sql/repeat.csv).

### How often do customer cohorts buy again?

25 observed first-purchase cohorts span 325 cohort-month cells. Later cohorts have shorter follow-up; absent future cells are unobserved, not zero retention.

Action to evaluate: Compare cohorts at equal maturity; flag incomplete last month. [Complete result](../../reports/exploratory/sql/cohorts.csv).

### Which known customers have high recency, frequency and value?

Output contains 5,878 groups/periods. First reported result: customer_id=18102; recency_days=0; frequency=145; monetary=5.81e+05; monetary_quartile=4.

Action to evaluate: Validate outreach rules on contemporary consented data. [Complete result](../../reports/exploratory/sql/rfm.csv).

### Which dates have no recorded positive sales?

135 calendar days had no positive recorded sales; the cause is unobserved.

Action to evaluate: Confirm whether gaps reflect closure or missing capture. [Complete result](../../reports/exploratory/sql/zero_days.csv).

### How concentrated are sales across product codes?

Output contains 5,304 groups/periods. First reported result: product_id=M; description=Manual; gross_sales=3.396e+05; sales_share=0.01654; cumulative_share=0.01654.

Action to evaluate: Review supply continuity for high-contribution codes. [Complete result](../../reports/exploratory/sql/contributions.csv).

## Exploratory findings

Mean recorded calendar-day sales: GBP 27,785.85. Dates with zero positive sales: 135. Daily autocorrelations: `{'1': 0.4177139012606214, '7': 0.6370805482559402, '14': 0.5468967155631113, '28': 0.514227091983814}`. The final source day and final month may be partial.

## Statistical findings

UK: 5,349 customers; other countries: 516. Mean customer-level invoice difference: GBP -293.98, bootstrap 95% CI [-377.48, -222.53].

Welch p=2.08674e-13, Holm p=2.08674e-13; Mann-Whitney p=7.50249e-44, Holm p=1.5005e-43.

Differences are associations conditional on identified customers. They do not establish an effect of geography. Review wholesale/customer mix before acting.

- Customers treated as independent; shared markets and unknown wholesale relationships may violate this.
- Country comparison is observational and not adjusted for mix, tenure or season.
- Welch permits unequal variances; heavy tails motivate the nonparametric sensitivity test.
- Holm correction covers the two explicitly reported geographic tests.
- Bootstrap intervals describe this sample era, not future prediction intervals.
- Seven-day moving blocks preserve local dependence but not all long-term seasonality.
- Paired tests/ANOVA/chi-square omitted because this predefined contrast does not require them.

## Machine learning methodology

Recorded gross sales in GBP on day t, not profit or latent demand. Immediately before day t; transaction aggregation available through t-1. Fixed-model rolling one-day-ahead holdout; past holdout outcomes become available as next-day lag inputs. Not a fixed-origin multi-step forecast.

|            |   rows | start               | end                 |
|:-----------|-------:|:--------------------|:--------------------|
| train      |    461 | 2009-12-29 00:00:00 | 2011-04-03 00:00:00 |
| validation |    107 | 2011-04-04 00:00:00 | 2011-07-19 00:00:00 |
| test       |    142 | 2011-07-20 00:00:00 | 2011-12-08 00:00:00 |

Preprocessing, category encoding, scaling and variance selection fit within training folds. Candidate selection and tuning use validation MAE; final refit combines train and validation only. Features exclude same-day sales/orders and post-event transaction details.

## Candidate comparison (validation, not independent test)

| model                  |   cv_train_MAE |   cv_train_MAE_sd |   validation_MAE |   validation_RMSE |   validation_R2 |   validation_WAPE |   validation_n |
|:-----------------------|---------------:|------------------:|-----------------:|------------------:|----------------:|------------------:|---------------:|
| ridge                  |       12838.3  |           5178.64 |          7387.09 |           10208.1 |      0.581947   |          0.321222 |            107 |
| random_forest          |        9638.56 |           3354.62 |          8074.04 |           11206.9 |      0.496134   |          0.351094 |            107 |
| hist_gradient_boosting |       10546.7  |           3454.61 |          8400.33 |           11446.1 |      0.474396   |          0.365283 |            107 |
| seasonal_naive         |       11116.3  |           2661.06 |         10898.8  |           15748   |      0.00505965 |          0.473928 |            107 |
| dummy_mean             |       15298    |           5963.28 |         12702.7  |           16011.4 |     -0.0285047  |          0.552366 |            107 |

Search winner parameters: `{'model__alpha': 100}`. Frozen model: **ridge**.

## Independent chronological holdout

|                |     MAE |    RMSE |        R2 |     WAPE |   n | MAPE_note                                                 |
|:---------------|--------:|--------:|----------:|---------:|----:|:----------------------------------------------------------|
| selected       | 11275.7 | 15433.2 |  0.602906 | 0.306962 | 142 | Omitted: genuine zero-sales days make MAPE inappropriate. |
| seasonal_naive | 12271.5 | 17802.8 |  0.4716   | 0.334071 | 142 | Omitted: genuine zero-sales days make MAPE inappropriate. |
| dummy_mean     | 21483.5 | 27087.8 | -0.223292 | 0.584852 | 142 | Omitted: genuine zero-sales days make MAPE inappropriate. |

MAPE is omitted because zero-sales days make it inappropriate. WAPE uses total absolute error divided by total observed gross sales. Performance is conditional on daily updates of observed lag inputs.

## Explainability

| feature      |   mae_increase_gbp |   repeat_sd_gbp |
|:-------------|-------------------:|----------------:|
| weekday      |           4332.13  |        454.155  |
| lag_orders_1 |           1866.25  |        476.068  |
| rolling_7    |           1418.4   |        285.613  |
| lag_7        |           1096.32  |        180.231  |
| lag_28       |            972.917 |        171.643  |
| lag_14       |            497.969 |         86.2185 |
| month        |            494.447 |        159.211  |
| rolling_28   |            281.466 |        249.49   |

Permutation MAE changes are post-evaluation sensitivities. Correlated lags, temporal dependence and unrealistic shuffled combinations prevent causal or directional conclusions.

## Visualization gallery

### Missing values by source field

![Missing values by source field](../../visualizations/anomalies/missing_bar.png)

Customer IDs are missing in 22.8% of source rows.

### Missingness across sampled source rows

![Missingness across sampled source rows](../../visualizations/anomalies/missing_matrix.png)

Display shows a seeded sample; totals use all rows.

### Joint missingness as percentage of all rows

![Joint missingness as percentage of all rows](../../visualizations/anomalies/missing_heatmap.png)

Cells use all source rows as the denominator.

### Signed source quantities and prices

![Signed source quantities and prices](../../visualizations/anomalies/source_outliers.png)

Statistical extremes remain; negative prices are separately quarantined. Isolation Forest is omitted because univariate rules are interpretable for these fields.

### Distribution of positive invoice values

![Distribution of positive invoice values](../../visualizations/distributions/invoice_distribution.png)

Median invoice-group value is GBP 302.78; 99th percentile is GBP 4,408.59.

### Basket distributions in six frequent markets

![Basket distributions in six frequent markets](../../visualizations/categories/country_baskets.png)

Boxes show within-market dispersion; hidden plotted fliers remain in all calculations.

### Sampled basket-value density by market

![Sampled basket-value density by market](../../visualizations/distributions/basket_violin.png)

Density uses a seeded sample of 5,000 positive invoice groups.

### Daily recorded sales and trailing trend

![Daily recorded sales and trailing trend](../../visualizations/time_series/daily_sales.png)

Daily gross sales range from GBP 0 to GBP 200,939; final source day may be partial.

### Monthly gross sales and cancellation value

![Monthly gross sales and cancellation value](../../visualizations/time_series/monthly_sales.png)

1 monthly period(s) are incomplete.

### Top ten countries by gross sales

![Top ten countries by gross sales](../../visualizations/categories/country_sales.png)

United Kingdom contributes 85.1%.

### Product-code contribution curve

![Product-code contribution curve](../../visualizations/categories/product_concentration.png)

The leading 20 codes contribute 13.8% of gross sales.

### Spearman association across invoice measures

![Spearman association across invoice measures](../../visualizations/correlations/invoice_correlations.png)

Invoice-derived measures share mathematical components; associations are not causal.

### Units and value in sampled invoices

![Units and value in sampled invoices](../../visualizations/relationships/units_value.png)

Log axes retain wholesale extremes and show variation in unit price and assortment.

### Sampled invoice relationships

![Sampled invoice relationships](../../visualizations/relationships/invoice_pairplot.png)

600 seeded sampled invoices; all three measures use log1p transformations.

### Observed customer purchase retention

![Observed customer purchase retention](../../visualizations/dashboards/cohort_retention.png)

Blank future cells are unobserved. First cohort is left-censored; final month is incomplete.

### Weekly sales pattern using all calendar days

![Weekly sales pattern using all calendar days](../../visualizations/time_series/weekday_sales.png)

Means include zero-record dates; no-record days do not prove absence of demand.

### Market contribution over time

![Market contribution over time](../../visualizations/categories/market_mix.png)

Each column uses that month's gross sales denominator; final month is partial.

### Customer-level difference with 95% bootstrap CI

![Customer-level difference with 95% bootstrap CI](../../visualizations/relationships/customer_difference_ci.png)

Difference GBP -293.98; interval [-377.48, -222.53]. Observational association, not a geographic treatment effect.

### One-day-ahead forecasts on untouched holdout

![One-day-ahead forecasts on untouched holdout](../../visualizations/machine_learning/holdout_forecast.png)

Selected holdout MAE: GBP 11,275.68; seasonal baseline MAE: GBP 12,271.49.

### Predicted versus observed holdout sales

![Predicted versus observed holdout sales](../../visualizations/machine_learning/actual_predicted.png)

Holdout R-squared is 0.603; extremes may remain poorly predicted.

### Holdout residual distribution and scale

![Holdout residual distribution and scale](../../visualizations/machine_learning/residuals.png)

Mean signed error is GBP 2,526.87.

### Frozen-model permutation sensitivity

![Frozen-model permutation sensitivity](../../visualizations/machine_learning/permutation_importance.png)

Largest observed sensitivity: weekday; correlated lags and calendar dependencies make this diagnostic non-causal.

## Business recommendations

Resolve customer identifier gaps, review ambiguous duplicates with source owners, investigate high-contribution markets/products, and validate cancellation workflows. Use the forecast only after contemporary shadow testing against the seasonal baseline. [Evidence and individual actions](../business_insights/insights.md).

## Power BI handoff

The exports include fact_sales, four dimensions, and forecast_evaluation with validated keys. [Import instructions](../../powerbi/power_query_steps.md) and [DAX measures](../../powerbi/dax_measures.md) describe the manual Desktop build. No .pbix file has been generated or validated.

## Limitations and future improvements

Single historical retailer; anonymous customers; uncertain source duplicate identity; no profit, inventory, marketing, weather, or holiday-calendar enrichment; service codes included; partial final day; no causal design; correlated observations; limited daily training history; no calibrated forecast intervals. Obtain contemporary source line IDs and operations calendars, test multi-year rolling origins, and evaluate conditional uncertainty before deployment.

## Reproducibility

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe main.py --all
```

Checkpoint digests cover source code, configuration, SQL, runtime dependencies, dependency manifests and artifact bytes. Changed dependencies force rebuilding from the earliest affected stage. Use --force to rerun selected stages. Acquisition reuses verified immutable raw files.