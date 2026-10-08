# Model card

Selected model: **ridge**. Predict next-day recorded gross sales in GBP immediately before that calendar day. Intended for historical operations research.

Training and preprocessing use past dates; expanding-window CV tunes training folds; validation selects the model; train plus validation refits it; the final chronological test is never used for tuning. Same-weekday and mean baselines are evaluated on identical holdout dates.

|                |     MAE |    RMSE |        R2 |     WAPE |   n | MAPE_note                                                 |
|:---------------|--------:|--------:|----------:|---------:|----:|:----------------------------------------------------------|
| selected       | 11275.7 | 15433.2 |  0.602906 | 0.306962 | 142 | Omitted: genuine zero-sales days make MAPE inappropriate. |
| seasonal_naive | 12271.5 | 17802.8 |  0.4716   | 0.334071 | 142 | Omitted: genuine zero-sales days make MAPE inappropriate. |
| dummy_mean     | 21483.5 | 27087.8 | -0.223292 | 0.584852 | 142 | Omitted: genuine zero-sales days make MAPE inappropriate. |

- Historical retailer only; no contemporary deployment validation.
- Gross recorded sales include service codes and ambiguous repeated lines.
- Few hundred daily observations despite over a million source lines.
- Extreme wholesale orders and seasonality can dominate errors.
- Nonnegative clipping is applied consistently during CV and inference.

No individual targeting, profit claims, causal interpretation, or calibrated prediction intervals. Inputs must comply with reports/model_performance/feature_contract.json. Monitor daily MAE/WAPE and calendar/lag drift on new data before any operational use. Joblib artifacts are executable Python objects; load only this project's trusted artifacts.