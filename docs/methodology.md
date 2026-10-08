# Analytical methodology

## Integrity and cleaning

Keep raw files immutable and hash every declared stage output. Validate source schema and report row issues before cleaning. Preserve Excel identifiers as strings and use sheet/row lineage keys. Quarantine impossible prices, nonfinite numerics, fractional quantities, missing essential keys and invalid dates; retain zero-price records and signed cancellations/adjustments.

Reconcile identical cross-sheet overlap copies using original eight-field equality and within-sheet occurrence order: keep the maximum multiplicity from any one sheet. Preserve uncertain within-sheet repeats and nonidentical variants. Quarantine is a separate dataset, never an unreported discard. Compare raw/cleaned profiles and report ambiguous-deduplication sensitivity.

## Business definitions and temporal comparisons

Gross sales are positive, non-cancellation line values. Signed value includes adjustments and is not an accounting revenue guarantee. No profit can be calculated. Complete calendar dates include zero recorded sales, which is different from known zero latent demand. Growth comparisons exclude incomplete months. Customer cohorts use first observed purchase, not customer creation; the earliest cohort is left-censored and recent cohorts have shorter follow-up. Latest product labels are for descriptive display only.

## Statistics

Predefine UK vs other-country customer-average invoice values. Use one observation per identified, single-country customer; anonymous/multi-country customers are excluded only from this contrast. Welch tests unequal means; Mann-Whitney tests distributional differences as a sensitivity analysis. Holm controls the two-test family. Report effect sizes, customer bootstrap difference intervals, and normality diagnostics. Descriptive Pearson/Spearman values are not causal evidence. Moving-block daily bootstrap intervals retain short-range dependence but do not capture all seasonality.

## Prediction

Forecast recorded gross sales immediately before day t from known calendar fields and outcomes through t−1. Exclude the final potentially incomplete source day. Use chronological 65%/15%/20% train/validation/test partitions after the 28-day warm-up. Training uses expanding-window TimeSeriesSplit, never random splits.

Compare mean and seasonal-naive baselines, Ridge, Random Forest and histogram boosting. Numeric median imputation/indicators, scaling, calendar one-hot encoding and zero-variance selection fit in each training fold. Mutual information is training-only descriptive diagnostics, not global feature filtering. Tuning uses training CV; validation chooses the candidate; refit train plus validation; evaluate frozen models once on final dates.

Test forecasts are rolling one-day-ahead with daily updates of realized lag inputs, not fixed-origin multi-step forecasts. Clip negative predictions to zero consistently in CV and inference. Report MAE, RMSE, R², WAPE; omit MAPE due to zero days. Test permutation importance is post-hoc only, not feedback for reselection. No calibrated uncertainty intervals are claimed. No entities are randomly split: the prediction unit is a calendar day for the same retailer.

## Computational scope

SQLite and Parquet keep million-line processing manageable. Most ML work operates on hundreds of daily observations. Two parallel workers and eight tuning draws are default limits. Descriptive charts use documented seeded samples where rendering all points would obscure patterns. Tests use small synthetic software fixtures only.

