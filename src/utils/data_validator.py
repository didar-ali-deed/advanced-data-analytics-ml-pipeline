"""Schema and relational checks without silently dropping records."""

import numpy as np
import pandas as pd


def validate_source(frame: pd.DataFrame, schema: dict) -> dict:
    """Return blocking schema errors and auditable row-level quality counts."""
    absent = sorted(set(schema["required"]) - set(frame.columns))
    report = {"rows": len(frame), "missing_columns": absent, "blocking": [], "issues": {}}
    if absent or frame.empty:
        report["blocking"].append("Missing required columns or empty dataset")
        return report
    for column in schema["not_null"]:
        report["issues"][f"{column}:null"] = int(frame[column].isna().sum())
    for column in schema["numeric"]:
        numeric = pd.to_numeric(frame[column], errors="coerce")
        report["issues"][f"{column}:invalid_numeric"] = int((~np.isfinite(numeric)).sum())
    dates = pd.to_datetime(frame[schema["date"]], errors="coerce")
    report["issues"]["invalid_date"] = int(dates.isna().sum())
    report["issues"]["out_of_date_range"] = int(
        ((dates < schema["date_min"]) | (dates > schema["date_max"])).sum()
    )
    report["issues"]["negative_price"] = int(
        (pd.to_numeric(frame["Price"], errors="coerce") < 0).sum()
    )
    report["issues"]["fractional_quantity"] = int(
        (pd.to_numeric(frame["Quantity"], errors="coerce").dropna() % 1 != 0).sum()
    )
    report["issues"]["blank_country"] = int(
        frame["Country"].astype("string").str.strip().eq("").sum()
    )
    if "line_id" in frame:
        if frame["line_id"].isna().any() or frame["line_id"].duplicated().any():
            report["blocking"].append("Synthetic source-row lineage keys are not unique/non-null")
    report["note"] = (
        "No documented closed country/product vocabulary. C-prefixed invoices are cancellations. "
        "Row-level issues remain in validated data for stage 07 quarantine."
    )
    return report


def assert_primary_key(frame: pd.DataFrame, key: str) -> None:
    """Reject null or repeated dimension keys."""
    if frame[key].isna().any() or frame[key].duplicated().any():
        raise ValueError(f"Primary key {key} must be unique and non-null")


def assert_foreign_key(fact: pd.DataFrame, dim: pd.DataFrame, key: str) -> None:
    """Require every fact key to match exactly one dimension key."""
    assert_primary_key(dim, key)
    orphan = ~fact[key].isin(dim[key])
    if orphan.any():
        raise ValueError(f"Foreign key {key}: {int(orphan.sum())} orphan rows")


def validate_inference(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Accept only numeric, finite engineered features, allowing missing lag inputs."""
    absent = set(columns) - set(frame.columns)
    if absent or frame.empty:
        raise ValueError(f"Invalid inference input: missing {sorted(absent)} or no rows")
    result = frame[columns].copy()
    for column in columns:
        values = pd.to_numeric(result[column], errors="coerce")
        invalid = result[column].notna() & values.isna()
        if invalid.any() or np.isinf(values).any():
            raise ValueError(f"Invalid numeric feature: {column}")
        result[column] = values
    for column, minimum, maximum in [("weekday", 0, 6), ("month", 1, 12)]:
        if column in result and (
            result[column].isna().any()
            or (~result[column].between(minimum, maximum)).any()
            or (result[column] % 1 != 0).any()
        ):
            raise ValueError(f"Unexpected category in {column}")
    return result
