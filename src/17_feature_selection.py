"""Stage 17: training-only diagnostics plus in-fold zero-variance selection."""

import pandas as pd
from sklearn.feature_selection import mutual_info_regression
from sklearn.impute import SimpleImputer

from utils.data_loader import read_frame, save_frame, write_json
from utils.preprocessing import FEATURES
from utils.runner import stage_cli


def run(ctx):
    """Report redundancy and MI without using held-out outcomes to choose predictors."""
    train = read_frame(ctx.path("data", "features", "train.parquet"))
    matrix = SimpleImputer(strategy="median", keep_empty_features=True).fit_transform(
        train[FEATURES]
    )
    scores = mutual_info_regression(
        matrix,
        train.target,
        random_state=ctx.config["seed"],
        discrete_features=[c in {"weekday", "month"} for c in FEATURES],
    )
    report = pd.DataFrame(
        {
            "feature": FEATURES,
            "mutual_information_train": scores,
            "train_unique": train[FEATURES].nunique().values,
        }
    )
    return [
        save_frame(
            report.sort_values("mutual_information_train", ascending=False),
            ctx.path("reports", "model_performance", "feature_selection.csv"),
        ),
        save_frame(
            train[FEATURES].corr().reset_index(),
            ctx.path("reports", "model_performance", "feature_correlations.csv"),
        ),
        write_json(
            {
                "selection": "VarianceThreshold inside the estimator pipeline and every CV fold",
                "allowlist": FEATURES,
                "mutual_information": "Training-only diagnostic; no supervised feature deletion is applied.",
                "redundancy": "Overlapping lags/rolling means retained; Ridge regularizes and tree models "
                "capture interactions. Correlated features complicate importance interpretation.",
            },
            ctx.path("reports", "model_performance", "feature_selection.json"),
        ),
    ]


if __name__ == "__main__":
    stage_cli(17)
