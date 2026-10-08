"""Business cleaning must preserve identifier semantics, cancellations and repeat lines."""

import pandas as pd

from utils.data_quality import duplicate_summary, missing_summary, outlier_flags
from utils.preprocessing import clean_transactions, standardize


def test_negative_price_quarantined_but_cancellation_retained(source, schema):
    accepted, quarantine, log = clean_transactions(source, schema)
    assert len(accepted) == 5 and len(quarantine) == 1
    assert "negative_price" in quarantine.iloc[0].quarantine_reason
    assert accepted.loc[accepted.Invoice.eq("C101"), "Quantity"].iloc[0] == -1
    assert log["accepted_rows"] + log["quarantined_rows"] == len(source)


def test_whitespace_identifiers_and_unknowns(source, schema):
    accepted, _, _ = clean_transactions(source, schema)
    result = standardize(accepted)
    assert result.iloc[0].customer_id == "00001"
    assert result.iloc[0].product_id == "001"
    assert result.iloc[0].description == "First item"
    assert result.iloc[3].customer_id == "UNKNOWN"
    assert result.iloc[3].description == "UNKNOWN"


def test_repeated_invoice_and_exact_business_lines_retained(source, schema):
    repeat = source.iloc[[0]].assign(line_id="test:99", source_row=99)
    source = pd.concat([source, repeat], ignore_index=True)
    accepted, _, log = clean_transactions(source, schema)
    assert log["ambiguous_duplicate_rows_retained"] == 2
    assert len(accepted) == 6
    summary = duplicate_summary(source, schema["required"])
    assert summary["exact_business_row_repeats"] == 1
    assert summary["duplicate_line_ids"] == 0


def test_all_null_and_constant_outliers():
    frame = pd.DataFrame({"empty": [None] * 4, "constant": [7] * 4})
    summary = missing_summary(frame).set_index("column")
    assert summary.loc["empty", "missing_pct"] == 100
    flags = outlier_flags(frame.constant)
    assert not flags[["iqr", "zscore", "mad", "percentile"]].any().any()


def test_overlapping_sheets_keep_maximum_line_multiplicity(source, schema):
    first = pd.concat([source.iloc[[0]], source.iloc[[0]]], ignore_index=True)
    first["line_id"] = ["a:2", "a:3"]
    first["source_sheet"] = "a"
    second = pd.concat([source.iloc[[0]]] * 3, ignore_index=True)
    second["line_id"] = ["b:2", "b:3", "b:4"]
    second["source_sheet"] = "b"
    combined = pd.concat([first, second], ignore_index=True)
    accepted, quarantine, log = clean_transactions(combined, schema)
    assert len(accepted) == 3
    assert len(quarantine) == 2
    assert log["reasons_overlap"]["overlapping_sheet_copy"] == 2


def test_bad_dates_fractional_units_and_blank_key(source, schema):
    source["InvoiceDate"] = source.InvoiceDate.astype(object)
    source.loc[0, "InvoiceDate"] = "broken"
    source["Quantity"] = source.Quantity.astype(float)
    source.loc[1, "Quantity"] = 1.5
    source.loc[2, "StockCode"] = " "
    _, quarantine, _ = clean_transactions(source, schema)
    assert len(quarantine) == 4
