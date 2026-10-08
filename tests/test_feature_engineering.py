"""Prove chronological causality, calendar checks and disjoint split boundaries."""

import pandas as pd
import pytest

from utils.preprocessing import FEATURES, chronological_split, engineer_features


def test_future_mutation_cannot_change_past_features(daily):
    original = engineer_features(daily)
    changed = daily.copy()
    changed.loc[80:, ["gross_sales", "orders"]] = 999999
    after = engineer_features(changed)
    # Features for day 80 still see only day 79 and earlier.
    mask = original.date <= daily.iloc[80].date
    pd.testing.assert_frame_equal(original.loc[mask, FEATURES], after.loc[mask, FEATURES])
    assert (
        original.loc[original.date.eq(daily.iloc[80].date), "target"].iloc[0]
        != after.loc[after.date.eq(daily.iloc[80].date), "target"].iloc[0]
    )


def test_feature_values_and_allowlist(daily):
    result = engineer_features(daily)
    row = result.iloc[0]
    assert row.lag_1 == daily.iloc[27].gross_sales
    assert row.lag_7 == daily.iloc[21].gross_sales
    assert row.rolling_7 == daily.iloc[21:28].gross_sales.mean()
    assert row.rolling_28 == daily.iloc[:28].gross_sales.mean()
    assert "target" not in FEATURES
    assert "gross_sales" not in FEATURES
    assert (
        engineer_features(daily, include_future=True).iloc[-1].target
        != engineer_features(daily, include_future=True).iloc[-1].target
    )  # NaN: no fabricated label


def test_disjoint_chronology_and_duplicate_calendar(daily):
    result = engineer_features(daily)
    blocks = chronological_split(result, 0.65, 0.15)
    assert blocks["train"].date.max() < blocks["validation"].date.min()
    assert blocks["validation"].date.max() < blocks["test"].date.min()
    assert sum(map(len, blocks.values())) == len(result)
    with pytest.raises(ValueError, match="contiguous"):
        engineer_features(daily.drop(index=50))
    with pytest.raises(ValueError, match="unique"):
        engineer_features(pd.concat([daily, daily.iloc[[0]]]))


def test_inference_future_date(daily):
    result = engineer_features(daily, include_future=True)
    assert result.iloc[-1].date == daily.date.max() + pd.Timedelta(days=1)
    assert result.iloc[-1].lag_1 == daily.iloc[-1].gross_sales
