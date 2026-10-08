"""Train-fold preprocessing and persisted forecast model helpers."""

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from utils.data_loader import read_frame
from utils.data_validator import validate_inference
from utils.preprocessing import FEATURES


class SeasonalNaive(RegressorMixin, BaseEstimator):
    """Same weekday last week, with a training median fallback for missing inputs."""

    def fit(self, X, y):
        """Store only a training-sample fallback."""
        self.fallback_ = float(np.median(y))
        self.n_features_in_ = X.shape[1]
        return self

    def predict(self, X):
        """Use the explicitly available seven-day lag."""
        return X["lag_7"].fillna(self.fallback_).to_numpy()


def nonnegative_mae_score(estimator, X, y):
    """Use the same nonnegative forecast policy during CV and final inference."""
    return -float(np.mean(np.abs(np.asarray(y) - np.maximum(0, estimator.predict(X)))))


def make_pipeline(estimator) -> Pipeline:
    """Fit all learned preprocessing and variance selection inside each training fold."""
    categories = ["weekday", "month"]
    numeric = [c for c in FEATURES if c not in categories]
    preprocessing = ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [
                        (
                            "impute",
                            SimpleImputer(
                                strategy="median", add_indicator=True, keep_empty_features=True
                            ),
                        ),
                        ("scale", StandardScaler()),
                    ]
                ),
                numeric,
            ),
            ("calendar", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categories),
        ]
    )
    return Pipeline(
        [
            ("preprocess", preprocessing),
            ("selection", VarianceThreshold()),
            ("model", estimator),
        ]
    )


def candidates(seed: int, n_jobs: int) -> dict:
    """Compare mean, regularized linear, bagged-tree, and boosted-tree approaches."""
    return {
        "seasonal_naive": SeasonalNaive(),
        "dummy_mean": make_pipeline(DummyRegressor()),
        "ridge": make_pipeline(Ridge(alpha=10)),
        "random_forest": make_pipeline(
            RandomForestRegressor(
                n_estimators=180, min_samples_leaf=3, random_state=seed, n_jobs=n_jobs
            )
        ),
        "hist_gradient_boosting": make_pipeline(
            HistGradientBoostingRegressor(
                max_iter=150, max_leaf_nodes=15, l2_regularization=10, random_state=seed
            )
        ),
    }


def splits(ctx, names=("train", "validation", "test")) -> dict:
    """Load fixed train/validation/test tables."""
    return {name: read_frame(ctx.path("data", "features", name + ".parquet")) for name in names}


def predict(model, frame: pd.DataFrame) -> np.ndarray:
    """Predict nonnegative observed gross sales using an identical inference policy."""
    return np.maximum(0, model.predict(validate_inference(frame, FEATURES)))


def save_model(model, path):
    """Atomically persist the complete fitted preprocessing and model pipeline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    joblib.dump(model, temporary)
    temporary.replace(path)
    return path
