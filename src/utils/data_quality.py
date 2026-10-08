"""Profiling and transparent anomaly flags."""

import numpy as np
import pandas as pd


def missing_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Return counts and percentages, including all-null columns."""
    return pd.DataFrame(
        {
            "column": frame.columns,
            "missing_count": frame.isna().sum().values,
            "missing_pct": frame.isna().mean().mul(100).values,
            "unique_count": frame.nunique(dropna=True).values,
            "dtype": frame.dtypes.astype(str).values,
        }
    )


def duplicate_summary(frame: pd.DataFrame, business_columns: list[str]) -> dict:
    """Separate repeated transaction lines from repeated order identifiers."""
    return {
        "rows": len(frame),
        "exact_business_row_repeats": int(frame.duplicated(business_columns).sum()),
        "repeated_invoice_rows": int(frame.duplicated(["Invoice"]).sum()),
        "duplicate_line_ids": int(frame["line_id"].duplicated().sum()),
        "policy": "Retain ambiguous repeated business lines; source row is the unique key.",
    }


def profile(frame: pd.DataFrame) -> dict:
    """Profile distributions, coverage, cardinality, and memory."""
    numeric = frame.select_dtypes(include="number")
    dates = frame.select_dtypes(include="datetime")
    return {
        "rows": len(frame),
        "columns": len(frame.columns),
        "memory_bytes": int(frame.memory_usage(deep=True).sum()),
        "missing": missing_summary(frame).to_dict("records"),
        "numeric": numeric.describe(percentiles=[0.01, 0.25, 0.5, 0.75, 0.99]).to_dict(),
        "skewness": numeric.skew().to_dict(),
        "kurtosis": numeric.kurt().to_dict(),
        "correlations": numeric.corr().to_dict(),
        "constant_columns": [c for c in frame if frame[c].nunique(dropna=True) <= 1],
        "high_cardinality": [c for c in frame if frame[c].nunique() > 0.5 * len(frame)],
        "date_coverage": {c: [str(dates[c].min()), str(dates[c].max())] for c in dates},
        "top_categories": {
            c: frame[c].value_counts(dropna=False).head(10).to_dict()
            for c in frame.select_dtypes(include=["object", "string", "category"])
        },
    }


def outlier_flags(series: pd.Series) -> pd.DataFrame:
    """Flag IQR, z-score, MAD, and percentile extremes; never remove them."""
    values = pd.to_numeric(series, errors="coerce")
    q1, q3 = values.quantile([0.25, 0.75])
    spread = q3 - q1
    median = values.median()
    mad = (values - median).abs().median()
    sd = values.std()
    return pd.DataFrame(
        {
            "iqr": (values < q1 - 1.5 * spread) | (values > q3 + 1.5 * spread),
            "zscore": (values - values.mean()).abs() > 3 * sd if sd > 0 else False,
            "mad": 0.6745 * (values - median).abs() / mad > 3.5 if mad > 0 else False,
            "percentile": (values < values.quantile(0.01)) | (values > values.quantile(0.99)),
            "nonfinite": ~np.isfinite(values),
        },
        index=series.index,
    )
