"""Stage 18: expanding-window CV on training data and separate validation selection."""

import pandas as pd
from sklearn.model_selection import TimeSeriesSplit, cross_validate

from utils.data_loader import save_frame, write_json
from utils.metrics import regression_metrics
from utils.modeling import candidates, nonnegative_mae_score, predict, save_model, splits
from utils.preprocessing import FEATURES
from utils.runner import stage_cli


def run(ctx):
    """Train justified candidates including a seasonal baseline without reading test labels."""
    blocks = splits(ctx, ("train", "validation"))
    train, validation = blocks["train"], blocks["validation"]
    models = candidates(ctx.config["seed"], ctx.config["model"]["n_jobs"])
    cv = TimeSeriesSplit(n_splits=ctx.config["model"]["cv_splits"])
    rows, outputs, folds = [], [], []
    for fold, (a, b) in enumerate(cv.split(train)):
        folds.append(
            {
                "fold": fold,
                "train_end": str(train.iloc[a].date.max()),
                "validation_start": str(train.iloc[b].date.min()),
                "train_rows": len(a),
                "validation_rows": len(b),
            }
        )
    for name, model in models.items():
        scores = cross_validate(
            model,
            train[FEATURES],
            train.target,
            cv=cv,
            scoring=nonnegative_mae_score,
            n_jobs=1,
            error_score="raise",
        )
        model.fit(train[FEATURES], train.target)
        metrics = regression_metrics(validation.target, predict(model, validation))
        rows.append(
            {
                "model": name,
                "cv_train_MAE": -scores["test_score"].mean(),
                "cv_train_MAE_sd": scores["test_score"].std(),
                **{f"validation_{k}": v for k, v in metrics.items() if k != "MAPE_note"},
            }
        )
        outputs.append(save_model(model, ctx.path("models", "trained", name + ".joblib")))
    comparison = pd.DataFrame(rows).sort_values("validation_MAE")
    outputs.extend(
        [
            save_frame(
                comparison, ctx.path("reports", "model_performance", "candidate_comparison.csv")
            ),
            write_json(
                {
                    "winner": comparison.iloc[0].model,
                    "selection_metric": "validation_MAE",
                    "cv_folds": folds,
                    "test_used": False,
                },
                ctx.path("models", "evaluation", "training_selection.json"),
            ),
        ]
    )
    return outputs


if __name__ == "__main__":
    stage_cli(18)
