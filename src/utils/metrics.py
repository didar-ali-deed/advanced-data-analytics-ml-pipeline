"""Regression metrics with explicitly defined denominators."""

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def regression_metrics(actual, predicted) -> dict:
    """Calculate MAE/RMSE/R2 and WAPE; omit unstable zero-denominator percentages."""
    actual, predicted = np.asarray(actual), np.asarray(predicted)
    denominator = np.abs(actual).sum()
    return {
        "MAE": mean_absolute_error(actual, predicted),
        "RMSE": np.sqrt(mean_squared_error(actual, predicted)),
        "R2": r2_score(actual, predicted),
        "WAPE": np.abs(actual - predicted).sum() / denominator if denominator > 0 else None,
        "n": len(actual),
        "MAPE_note": "Omitted: genuine zero-sales days make MAPE inappropriate.",
    }
