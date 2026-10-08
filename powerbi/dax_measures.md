# DAX measures

Create these explicit measures in a dedicated Measures table. Monetary values use GBP currency formatting; ratios use percentage formatting. Flags are Boolean after the Power Query steps. These definitions match pipeline calculations.

```dax
Gross Sales = SUM(fact_sales[gross_sales])

Signed Transaction Value = SUM(fact_sales[net_value])

Cancellation Value = SUM(fact_sales[cancellation_value])

Cancellation to Sales Ratio = DIVIDE([Cancellation Value], [Gross Sales])

Sale Units =
CALCULATE(SUM(fact_sales[quantity]), fact_sales[is_sale] = TRUE())

Sale Invoices =
CALCULATE(DISTINCTCOUNT(fact_sales[invoice_id]), fact_sales[is_sale] = TRUE())

Average Invoice Value = DIVIDE([Gross Sales], [Sale Invoices])

Known Buyers =
CALCULATE(
    DISTINCTCOUNT(fact_sales[customer_id]),
    fact_sales[is_sale] = TRUE(),
    fact_sales[customer_id] <> "UNKNOWN"
)

Anonymous Sales =
CALCULATE([Gross Sales], fact_sales[customer_id] = "UNKNOWN")

Anonymous Sales Share = DIVIDE([Anonymous Sales], [Gross Sales])

Accepted Lines = COUNTROWS(fact_sales)

Ambiguous Repeat Lines =
CALCULATE(COUNTROWS(fact_sales), fact_sales[ambiguous_duplicate] = TRUE())

Zero Price Lines =
CALCULATE(COUNTROWS(fact_sales), fact_sales[unit_price] = 0)

Non Cancellation Adjustment Value =
CALCULATE([Signed Transaction Value], fact_sales[is_adjustment] = TRUE())

Average Daily Recorded Sales =
AVERAGEX(VALUES(dim_date[date]), COALESCE([Gross Sales], 0))

Trailing Seven Day Sales =
VAR EndDate = MAX(dim_date[date])
RETURN
CALCULATE([Gross Sales], DATESINPERIOD(dim_date[date], EndDate, -7, DAY))

Cumulative Sales in Selection =
VAR EndDate = MAX(dim_date[date])
RETURN
CALCULATE(
    [Gross Sales],
    FILTER(ALLSELECTED(dim_date[date]), dim_date[date] <= EndDate)
)

Country Sales Contribution =
DIVIDE([Gross Sales], CALCULATE([Gross Sales], REMOVEFILTERS(dim_country)))

Forecast MAE =
AVERAGEX(forecast_evaluation, ABS(forecast_evaluation[target] - forecast_evaluation[selected]))

Forecast RMSE =
SQRT(AVERAGEX(
    forecast_evaluation,
    POWER(forecast_evaluation[target] - forecast_evaluation[selected], 2)
))

Forecast WAPE =
DIVIDE(
    SUMX(forecast_evaluation, ABS(forecast_evaluation[target] - forecast_evaluation[selected])),
    SUM(forecast_evaluation[target])
)

Seasonal Baseline MAE =
AVERAGEX(
    forecast_evaluation,
    ABS(forecast_evaluation[target] - forecast_evaluation[seasonal_naive])
)

MAE Improvement over Seasonal Baseline = [Seasonal Baseline MAE] - [Forecast MAE]
```

The cancellation ratio is a ratio of recorded values in the selected period, not an order-return probability: cancellation dates may differ from purchase dates. Average invoice value uses distinct sale invoice IDs, while the exploratory invoice table uses invoice/customer/country groups. There is no cost data, so profit/margin measures are deliberately absent.

Use the generated SQL `growth.csv` and `yoy.csv` for complete-month growth comparisons; the last source month is incomplete. Forecast measures must only be filtered by the calendar, not market or product dimensions.

