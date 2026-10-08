"""Stage 20: evaluate frozen final models on chronological holdout dates."""

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from utils.data_loader import read_json, save_frame, write_json, write_text
from utils.metrics import regression_metrics
from utils.modeling import predict, splits
from utils.runner import stage_cli
from utils.visualization import Charts


def run(ctx):
    """Report independent test performance separately from training CV and validation."""
    test = splits(ctx)["test"]
    selection = read_json(ctx.path("models", "evaluation", "tuning_summary.json"))
    predictions = test[["date", "target"]].copy()
    metrics = {}
    for name, file in [
        ("selected", "final_model"),
        ("seasonal_naive", "final_seasonal_baseline"),
        ("dummy_mean", "final_dummy_baseline"),
    ]:
        model = joblib.load(ctx.path("models", "trained", file + ".joblib"))
        predictions[name] = predict(model, test)
        metrics[name] = regression_metrics(test.target, predictions[name])
    predictions["residual"] = predictions.target - predictions.selected
    predictions["weekday"] = predictions.date.dt.dayofweek
    by_weekday = (
        predictions.groupby("weekday")
        .apply(
            lambda group: pd.Series(regression_metrics(group.target, group.selected)).drop(
                "MAPE_note"
            ),
            include_groups=False,
        )
        .reset_index()
    )
    report = {
        "selected_model": selection["selected_model"],
        "holdout_start": str(test.date.min()),
        "holdout_end": str(test.date.max()),
        "metrics": metrics,
        "protocol": "Fixed-model rolling one-day-ahead evaluation; prior realized days update lag inputs.",
        "selection_independent_of_test": True,
        "forecast_horizon_days": 1,
        "limitations": [
            "Historical retailer only; no contemporary deployment validation.",
            "Gross recorded sales include service codes and ambiguous repeated lines.",
            "Few hundred daily observations despite over a million source lines.",
            "Extreme wholesale orders and seasonality can dominate errors.",
            "Nonnegative clipping is applied consistently during CV and inference.",
        ],
    }
    charts = Charts(ctx, 20)
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(predictions.date, predictions.target, label="Observed", color="#147D92")
    ax.plot(predictions.date, predictions.selected, label="Selected forecast", color="#E19B42")
    ax.plot(
        predictions.date, predictions.seasonal_naive, label="Same weekday last week", alpha=0.45
    )
    ax.set(xlabel="Holdout date", ylabel="Recorded gross sales (GBP)")
    ax.legend()
    charts.save(
        fig,
        "machine_learning",
        "holdout_forecast",
        "One-day-ahead forecasts on untouched holdout",
        "How closely do predictions track observed sales?",
        f"Selected holdout MAE: GBP {metrics['selected']['MAE']:,.2f}; "
        f"seasonal baseline MAE: GBP {metrics['seasonal_naive']['MAE']:,.2f}.",
    )
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(predictions.target, predictions.selected, alpha=0.6, s=18)
    limit = max(predictions.target.max(), predictions.selected.max())
    ax.plot([0, limit], [0, limit], "--", color="gray")
    ax.set(xlabel="Observed gross sales (GBP)", ylabel="Predicted gross sales (GBP)")
    charts.save(
        fig,
        "machine_learning",
        "actual_predicted",
        "Predicted versus observed holdout sales",
        "Where do forecasts deviate from the identity line?",
        f"Holdout R-squared is {metrics['selected']['R2']:.3f}; extremes may remain poorly predicted.",
    )
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    sns.histplot(predictions.residual, bins=25, ax=axes[0])
    axes[0].set(xlabel="Actual minus forecast (GBP)", ylabel="Holdout days")
    axes[1].scatter(predictions.selected, predictions.residual, alpha=0.6, s=15)
    axes[1].axhline(0, color="gray", linestyle="--")
    axes[1].set(xlabel="Forecast sales (GBP)", ylabel="Actual minus forecast (GBP)")
    charts.save(
        fig,
        "machine_learning",
        "residuals",
        "Holdout residual distribution and scale",
        "Are forecast errors systematically biased or size dependent?",
        f"Mean signed error is GBP {predictions.residual.mean():,.2f}.",
    )
    card = (
        "# Model card\n\n"
        f"Selected model: **{selection['selected_model']}**. Predict next-day recorded gross sales in GBP "
        "immediately before that calendar day. Intended for historical operations research.\n\n"
        "Training and preprocessing use past dates; expanding-window CV tunes training folds; validation "
        "selects the model; train plus validation refits it; the final chronological test is never used "
        "for tuning. Same-weekday and mean baselines are evaluated on identical holdout dates.\n\n"
        + pd.DataFrame(metrics).T.to_markdown()
        + "\n\n"
        + "\n".join("- " + item for item in report["limitations"])
        + "\n\nNo individual targeting, profit claims, causal interpretation, or calibrated prediction "
        "intervals. Inputs must comply with reports/model_performance/feature_contract.json. "
        "Monitor daily MAE/WAPE and calendar/lag drift on new data before any operational use. "
        "Joblib artifacts are executable Python objects; load only this project's trusted artifacts."
    )
    return [
        save_frame(predictions, ctx.path("models", "evaluation", "holdout_predictions.csv")),
        save_frame(by_weekday, ctx.path("models", "evaluation", "holdout_by_weekday.csv")),
        write_json(report, ctx.path("models", "evaluation", "holdout_metrics.json")),
        write_text(card, ctx.path("models", "model_card.md")),
    ] + charts.finish()


if __name__ == "__main__":
    stage_cli(20)
