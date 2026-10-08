"""Preprocessing fits train only and handles valid unseen calendar categories."""

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import Ridge

from utils.metrics import regression_metrics
from utils.modeling import make_pipeline, predict, save_model
from utils.preprocessing import FEATURES, chronological_split, engineer_features
from utils.statistics import holm_adjust


def test_preprocessing_fit_is_training_only_and_persisted(daily, tmp_path):
    blocks = chronological_split(engineer_features(daily), 0.65, 0.15)
    train, test = blocks["train"], blocks["test"]
    model = make_pipeline(Ridge()).fit(train[FEATURES], train.target)
    numeric = [c for c in FEATURES if c not in {"weekday", "month"}]
    fitted = model.named_steps["preprocess"].named_transformers_["numeric"]
    np.testing.assert_allclose(fitted["impute"].statistics_, train[numeric].median())
    path = save_model(model, tmp_path / "model.joblib")
    np.testing.assert_allclose(predict(model, test), predict(joblib.load(path), test))
    assert (predict(model, test) >= 0).all()


def test_unseen_valid_month_and_missing_lag_inference(daily):
    frame = engineer_features(daily)
    training = frame.iloc[:35]
    model = make_pipeline(Ridge()).fit(training[FEATURES], training.target)
    unseen = frame.iloc[[-1]][FEATURES].copy()
    unseen["month"] = 12  # Valid category unseen in this training block.
    unseen["lag_1"] = np.nan
    assert np.isfinite(predict(model, unseen)).all()
    unseen["lag_7"] = "invalid"
    with pytest.raises(ValueError, match="numeric"):
        predict(model, unseen)


def test_variance_selector_and_all_null_column(daily):
    frame = engineer_features(daily)
    frame["lag_1"] = np.nan
    frame["lag_14"] = 5
    model = make_pipeline(Ridge()).fit(frame[FEATURES], frame.target)
    assert np.isfinite(predict(model, frame)).all()


def test_zero_denominator_metrics_and_holm():
    scores = regression_metrics(pd.Series([0, 0]), [1, 1])
    assert scores["WAPE"] is None
    assert scores["MAE"] == 1
    assert holm_adjust([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
