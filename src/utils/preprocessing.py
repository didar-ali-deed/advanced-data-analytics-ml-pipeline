"""Deterministic business rules, relational transformation, and causal-time features."""

import numpy as np
import pandas as pd

from utils.data_validator import assert_foreign_key, assert_primary_key

COLUMN_MAP = {
    "Invoice": "invoice_id",
    "StockCode": "product_id",
    "Description": "description",
    "Quantity": "quantity",
    "InvoiceDate": "invoice_date",
    "Price": "unit_price",
    "Customer ID": "customer_id",
    "Country": "country",
}
FEATURES = [
    "weekday",
    "month",
    "day_of_year_sin",
    "day_of_year_cos",
    "lag_1",
    "lag_7",
    "lag_14",
    "lag_28",
    "rolling_7",
    "rolling_28",
    "rolling_std_7",
    "lag_orders_1",
    "trend_7_28",
]


def clean_text(series: pd.Series) -> pd.Series:
    """Normalize whitespace without changing meaningful identifiers."""
    return series.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)


def clean_transactions(frame: pd.DataFrame, schema: dict) -> tuple:
    """Quarantine impossible records; preserve cancellations and ambiguous duplicates."""
    clean = frame.copy()
    # The source sheets overlap in December 2010. Match exact raw business rows
    # by their occurrence within a sheet, keeping the maximum multiplicity across
    # sheets. Thus two legitimate identical lines stay two, even if both are copied.
    occurrence = frame.groupby(
        ["source_sheet"] + schema["required"], dropna=False, sort=False
    ).cumcount()
    overlap_copy = frame.assign(_occurrence=occurrence).duplicated(
        schema["required"] + ["_occurrence"], keep="first"
    )
    reasons = pd.Series("", index=clean.index, dtype="string")
    corrected = {}
    for column in ["Invoice", "StockCode", "Description", "Country"]:
        normalized = clean_text(clean[column]).replace("", pd.NA)
        corrected[column] = int(
            (normalized.fillna("") != clean[column].astype("string").fillna("")).sum()
        )
        clean[column] = normalized
    clean["InvoiceDate"] = pd.to_datetime(clean["InvoiceDate"], errors="coerce")
    for column in ["Quantity", "Price"]:
        clean[column] = pd.to_numeric(clean[column], errors="coerce")
    rules = {
        "overlapping_sheet_copy": overlap_copy,
        "missing_required": clean[schema["not_null"]].isna().any(axis=1),
        "invalid_numeric": ~np.isfinite(clean["Quantity"]) | ~np.isfinite(clean["Price"]),
        "negative_price": clean["Price"] < 0,
        "fractional_quantity": clean["Quantity"] % 1 != 0,
        "invalid_date": clean["InvoiceDate"].isna()
        | (clean["InvoiceDate"] < schema["date_min"])
        | (clean["InvoiceDate"] > schema["date_max"]),
    }
    for label, mask in rules.items():
        reasons.loc[mask] = reasons.loc[mask] + label + ";"
    quarantine = clean.loc[reasons.ne("")].assign(quarantine_reason=reasons[reasons.ne("")])
    accepted = clean.loc[reasons.eq("")].copy()
    accepted["Description"] = accepted["Description"].fillna("UNKNOWN")
    # Decimal suffixes originate from Excel numeric IDs, never strip leading zeros.
    accepted["Customer ID"] = (
        clean_text(accepted["Customer ID"]).str.replace(r"\.0$", "", regex=True).fillna("UNKNOWN")
    )
    accepted["ambiguous_duplicate"] = accepted.duplicated(schema["required"], keep=False)
    accepted["is_cancellation"] = accepted["Invoice"].str.upper().str.startswith("C")
    accepted["is_adjustment"] = (accepted["Quantity"] < 0) & ~accepted["is_cancellation"]
    log = {
        "original_rows": len(frame),
        "accepted_rows": len(accepted),
        "quarantined_rows": len(quarantine),
        "removed_rows": 0,
        "reasons_overlap": {k: int(v.sum()) for k, v in rules.items()},
        "text_values_corrected": corrected,
        "unknown_customers": int(accepted["Customer ID"].eq("UNKNOWN").sum()),
        "unknown_descriptions": int(accepted["Description"].eq("UNKNOWN").sum()),
        "ambiguous_duplicate_rows_retained": int(accepted["ambiguous_duplicate"].sum()),
        "policy": "Exact cross-sheet copies are quarantined by multiset overlap reconciliation; "
        "ambiguous within-sheet repeats remain. All rows reconcile to accepted + quarantine.",
    }
    if len(accepted) + len(quarantine) != len(frame):
        raise AssertionError("Cleaning row reconciliation failed")
    return accepted, quarantine, log


def standardize(frame: pd.DataFrame) -> pd.DataFrame:
    """Use snake_case, string identifiers, GBP, and source-local naive timestamps."""
    result = frame.rename(columns=COLUMN_MAP).copy()
    for column in ["invoice_id", "product_id", "customer_id"]:
        result[column] = clean_text(result[column]).str.replace(r"\.0$", "", regex=True)
    result["country"] = clean_text(result["country"])
    result["description"] = clean_text(result["description"])
    result["quantity"] = result["quantity"].astype("int64")
    result["unit_price"] = result["unit_price"].astype("float64")
    result["invoice_date"] = pd.to_datetime(result["invoice_date"])
    return result


def transform(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create signed and gross line values plus a complete daily observation calendar."""
    lines = frame.copy()
    lines["date"] = lines["invoice_date"].dt.strftime("%Y-%m-%d")
    lines["month"] = lines["invoice_date"].dt.strftime("%Y-%m")
    lines["weekday"] = lines["invoice_date"].dt.dayofweek
    lines["hour"] = lines["invoice_date"].dt.hour
    lines["net_value"] = lines["quantity"] * lines["unit_price"]
    lines["is_sale"] = (
        (lines["quantity"] > 0) & (lines["unit_price"] > 0) & ~lines["is_cancellation"]
    )
    lines["gross_sales"] = lines["net_value"].where(lines["is_sale"], 0)
    lines["cancellation_value"] = (-lines["net_value"]).where(
        lines["is_cancellation"] & (lines["net_value"] < 0), 0
    )
    daily = lines.groupby("date").agg(
        gross_sales=("gross_sales", "sum"),
        net_value=("net_value", "sum"),
        cancellation_value=("cancellation_value", "sum"),
        observed_lines=("line_id", "size"),
    )
    orders = lines.loc[lines["is_sale"]].groupby("date")["invoice_id"].nunique()
    daily["orders"] = orders
    daily.index = pd.to_datetime(daily.index)
    calendar = pd.date_range(daily.index.min(), daily.index.max(), freq="D", name="date")
    daily = daily.reindex(calendar).fillna(0).reset_index()
    daily["has_records"] = daily["observed_lines"] > 0
    daily["rolling_7_sales"] = daily["gross_sales"].rolling(7, min_periods=1).mean()
    daily["cumulative_sales"] = daily["gross_sales"].cumsum()
    daily["daily_growth"] = (
        daily["gross_sales"].pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)
    )
    return lines, daily


def build_star(lines: pd.DataFrame) -> tuple[dict, dict]:
    """Derive dimensions with deterministic keys and checked many-to-one joins."""
    assert_primary_key(lines, "line_id")
    ordered = lines.sort_values(["invoice_date", "line_id"])
    products = ordered.drop_duplicates("product_id", keep="last")[["product_id", "description"]]
    customers = pd.DataFrame({"customer_id": sorted(lines["customer_id"].unique())})
    countries = pd.DataFrame({"country": sorted(lines["country"].unique())})
    countries["country_id"] = np.arange(1, len(countries) + 1)
    dates = pd.DataFrame(
        {
            "date": pd.date_range(
                lines["invoice_date"].min().normalize(), lines["invoice_date"].max().normalize()
            )
        }
    )
    dates["year"] = dates["date"].dt.year
    dates["month_number"] = dates["date"].dt.month
    dates["weekday"] = dates["date"].dt.dayofweek
    dates["date"] = dates["date"].dt.strftime("%Y-%m-%d")
    merged = lines.merge(
        countries, on="country", how="left", validate="many_to_one", indicator=True
    )
    if not merged["_merge"].eq("both").all() or len(merged) != len(lines):
        raise ValueError("Integration multiplied or lost rows")
    columns = [
        "line_id",
        "invoice_id",
        "product_id",
        "customer_id",
        "country_id",
        "date",
        "invoice_date",
        "quantity",
        "unit_price",
        "net_value",
        "gross_sales",
        "cancellation_value",
        "is_sale",
        "is_cancellation",
        "is_adjustment",
        "ambiguous_duplicate",
        "hour",
    ]
    fact = merged[columns].copy()
    for dim, key in [
        (products, "product_id"),
        (customers, "customer_id"),
        (countries, "country_id"),
        (dates, "date"),
    ]:
        assert_foreign_key(fact, dim, key)
    if not np.isclose(fact["net_value"].sum(), lines["net_value"].sum()):
        raise ValueError("Value reconciliation failed")
    tables = {
        "fact_sales": fact,
        "dim_product": products,
        "dim_customer": customers,
        "dim_country": countries,
        "dim_date": dates,
    }
    report = {
        "input_rows": len(lines),
        "output_rows": len(fact),
        "orphan_rows": 0,
        "signed_value_before": lines["net_value"].sum(),
        "signed_value_after": fact["net_value"].sum(),
        "dimension_rows": {k: len(v) for k, v in tables.items() if k != "fact_sales"},
        "product_description_policy": "Latest observed description, descriptive use only.",
        "provenance": "All tables derived from one UCI workbook; no independent external enrichment.",
    }
    return tables, report


def engineer_features(daily: pd.DataFrame, include_future: bool = False) -> pd.DataFrame:
    """Predict day t from information through day t-1; no unshifted outcomes enter X."""
    frame = daily.sort_values("date").copy()
    frame["date"] = pd.to_datetime(frame["date"])
    if (
        frame["date"].duplicated().any()
        or not frame["date"].diff().dropna().eq(pd.Timedelta(days=1)).all()
    ):
        raise ValueError("Daily calendar must be unique and contiguous")
    if include_future:
        next_row = {"date": frame["date"].max() + pd.Timedelta(days=1)}
        frame = pd.concat([frame, pd.DataFrame([next_row])], ignore_index=True)
    frame["weekday"] = frame["date"].dt.dayofweek
    frame["month"] = frame["date"].dt.month
    angle = 2 * np.pi * frame["date"].dt.dayofyear / 365.25
    frame["day_of_year_sin"], frame["day_of_year_cos"] = np.sin(angle), np.cos(angle)
    for lag in [1, 7, 14, 28]:
        frame[f"lag_{lag}"] = frame["gross_sales"].shift(lag)
    past = frame["gross_sales"].shift(1)
    frame["rolling_7"] = past.rolling(7, min_periods=7).mean()
    frame["rolling_28"] = past.rolling(28, min_periods=28).mean()
    frame["rolling_std_7"] = past.rolling(7, min_periods=7).std()
    frame["lag_orders_1"] = frame["orders"].shift(1)
    frame["trend_7_28"] = frame["rolling_7"] / frame["rolling_28"].replace(0, np.nan)
    frame["target"] = frame["gross_sales"]
    return frame.loc[frame.index >= 28, ["date", "target"] + FEATURES].reset_index(drop=True)


def chronological_split(frame: pd.DataFrame, train: float, validation: float) -> dict:
    """Assign disjoint chronological blocks without shuffling."""
    frame = frame.sort_values("date").reset_index(drop=True)
    if frame["date"].duplicated().any():
        raise ValueError("Repeated forecast dates")
    a, b = int(len(frame) * train), int(len(frame) * (train + validation))
    blocks = {"train": frame.iloc[:a], "validation": frame.iloc[a:b], "test": frame.iloc[b:]}
    if any(part.empty for part in blocks.values()):
        raise ValueError("Insufficient history for train/validation/test")
    return blocks
