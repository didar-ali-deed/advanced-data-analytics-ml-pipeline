"""Reconcile monetary definitions and explicitly zero-filled calendar dates."""

import pytest

from utils.preprocessing import clean_transactions, standardize, transform


def test_signed_gross_cancellation_and_calendar(source, schema):
    cleaned, _, _ = clean_transactions(source, schema)
    lines, daily = transform(standardize(cleaned))
    assert lines.gross_sales.sum() == pytest.approx(43)
    assert lines.net_value.sum() == pytest.approx(33)
    assert lines.cancellation_value.sum() == pytest.approx(10)
    assert len(daily) == 3
    assert daily.iloc[1].gross_sales == 0
    assert not daily.iloc[1].has_records
    assert daily.iloc[-1].cumulative_sales == 43


def test_cancellation_with_positive_quantity_not_sale(source, schema):
    source.loc[2, "Quantity"] = 1
    clean, _, _ = clean_transactions(source, schema)
    lines, _ = transform(standardize(clean))
    row = lines.loc[lines.invoice_id.eq("C101")].iloc[0]
    assert row.gross_sales == 0
    assert row.net_value == 10
