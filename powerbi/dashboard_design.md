# Dashboard design

Use a consistent navy/teal palette with amber for forecasts and muted red for cancellations. Label every value in GBP or percent. Prefer explicit measures over implicit sums.

1. **Executive Overview:** Gross Sales, Cancellation Value, Sale Invoices, Average Invoice Value, Known Buyers; monthly line chart and country contribution bars. Date and country slicers. Add source dates and a partial-final-month note.
2. **Operational Performance:** daily sales and trailing seven-day series; weekday averages; cancellation-value ratios by market. Explain that zero-record dates do not establish closure.
3. **Customer and Product Analysis:** top product codes, contribution curve, known-buyer counts, anonymous sales share. Link the cohort chart and state cohort censoring. Include service-code limitations.
4. **Trends and Segmentation:** complete-month growth outputs, geographic mix, RFM snapshot. Never compare new cohorts with mature cohorts without matching elapsed months.
5. **Data Quality and Predictive Insights:** cleaning/quarantine counts from reports, recorded duplicate sensitivity, actual/predicted daily sales, MAE/RMSE/WAPE and seasonal-baseline MAE. Disable product/customer/country filtering for the total-sales forecast.

Use 16:9 pages, a visible date range, consistent KPI formats, and accessible labels. Add evidence links to the generated SQL CSVs and model card. Drillthrough should preserve grain. Test totals against `reports/exploratory/sql/overview.csv` and `models/evaluation/holdout_metrics.json`.

This repository supplies validated exports and specifications, not a generated or validated PBIX.

