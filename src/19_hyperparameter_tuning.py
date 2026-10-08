"""Stage 19: bounded time-series search followed by frozen model selection."""

import joblib
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit

from utils.data_loader import read_frame, save_frame, write_json
from utils.metrics import regression_metrics
from utils.modeling import candidates, nonnegative_mae_score, predict, save_model, splits
from utils.preprocessing import FEATURES
from utils.runner import stage_cli


def run(ctx):
    """Tune only training folds; compare on validation, then refit before unlocking test."""
    blocks = splits(ctx, ("train", "validation"))
    train, validation = blocks["train"], blocks["validation"]
    comparison = read_frame(ctx.path("reports", "model_performance", "candidate_comparison.csv"))
    tunable = comparison.loc[~comparison.model.isin(["dummy_mean", "seasonal_naive"])]
    challenger = tunable.iloc[0].model
    spaces = {
        "ridge": {"model__alpha": [0.01, 0.1, 1, 10, 100, 1000, 10000, 100000]},
        "random_forest": {
            "model__max_depth": [3, 6, 10, None],
            "model__min_samples_leaf": [2, 5, 10],
            "model__max_features": [0.7, 1.0],
        },
        "hist_gradient_boosting": {
            "model__learning_rate": [0.03, 0.07, 0.12],
            "model__max_leaf_nodes": [7, 15, 31],
            "model__l2_regularization": [1, 10, 100],
        },
    }
    search = RandomizedSearchCV(
        candidates(ctx.config["seed"], 1)[challenger],
        spaces[challenger],
        n_iter=ctx.config["model"]["search_iterations"],
        scoring=nonnegative_mae_score,
        cv=TimeSeriesSplit(n_splits=ctx.config["model"]["cv_splits"]),
        n_jobs=ctx.config["model"]["n_jobs"],
        random_state=ctx.config["seed"],
        refit=True,
        error_score="raise",
    )
    search.fit(train[FEATURES], train.target)
    challenger_mae = regression_metrics(
        validation.target, predict(search.best_estimator_, validation)
    )["MAE"]
    incumbent_name = comparison.iloc[0].model
    incumbent_mae = float(comparison.iloc[0].validation_MAE)
    if challenger_mae < incumbent_mae:
        name, selected = challenger + "_tuned", search.best_estimator_
    else:
        name = incumbent_name
        selected = joblib.load(ctx.path("models", "trained", incumbent_name + ".joblib"))
    combined = pd.concat([train, validation], ignore_index=True)
    final_model = clone(selected).fit(combined[FEATURES], combined.target)
    baseline = candidates(ctx.config["seed"], 1)["seasonal_naive"].fit(
        combined[FEATURES], combined.target
    )
    dummy = candidates(ctx.config["seed"], 1)["dummy_mean"].fit(combined[FEATURES], combined.target)
    return [
        save_frame(
            pd.DataFrame(search.cv_results_), ctx.path("models", "evaluation", "search_results.csv")
        ),
        save_model(final_model, ctx.path("models", "trained", "final_model.joblib")),
        save_model(baseline, ctx.path("models", "trained", "final_seasonal_baseline.joblib")),
        save_model(dummy, ctx.path("models", "trained", "final_dummy_baseline.joblib")),
        write_json(
            {
                "selected_model": name,
                "challenger": challenger,
                "best_parameters": search.best_params_,
                "best_train_cv_MAE": -search.best_score_,
                "challenger_validation_MAE": challenger_mae,
                "incumbent_validation_MAE": incumbent_mae,
                "incumbent": incumbent_name,
                "selection": "Lowest validation MAE before test access",
                "refit_rows": len(combined),
                "refit_end": str(combined.date.max()),
                "test_used": False,
            },
            ctx.path("models", "evaluation", "tuning_summary.json"),
        ),
    ]


if __name__ == "__main__":
    stage_cli(19)
