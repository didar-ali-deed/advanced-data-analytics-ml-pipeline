"""Stage 16: build chronological one-day-ahead examples with a strict feature allowlist."""

from utils.data_loader import read_frame, save_frame, write_json
from utils.preprocessing import FEATURES, chronological_split, engineer_features
from utils.runner import stage_cli


def run(ctx):
    """Exclude the potentially partial final day and retain it as an unscored replay date."""
    daily = read_frame(ctx.path("data", "processed", "daily.parquet"))
    history = daily.iloc[:-1].copy()
    engineered = engineer_features(history, include_future=True)
    observed = engineered.loc[engineered.target.notna()].copy()
    parts = chronological_split(
        observed, ctx.config["model"]["train_fraction"], ctx.config["model"]["validation_fraction"]
    )
    if len(parts["train"]) < ctx.config["model"]["min_training_days"]:
        raise ValueError(
            "Insufficient training history; change dataset or min_training_days explicitly"
        )
    future = engineered.loc[engineered.target.isna()].drop(columns="target")
    outputs = [
        save_frame(part, ctx.path("data", "features", name + ".parquet"))
        for name, part in parts.items()
    ]
    outputs += [
        save_frame(future, ctx.path("data", "features", "inference_input.csv")),
        save_frame(
            parts["test"].head(5).drop(columns="target"),
            ctx.path("data", "features", "sample_inference.csv"),
        ),
        write_json(
            {
                "target": "Recorded gross sales in GBP on day t, not profit or latent demand",
                "prediction_time": "Immediately before day t; transaction aggregation available through t-1",
                "features": FEATURES,
                "maximum_lag_days": 28,
                "split": {
                    name: {
                        "rows": len(part),
                        "start": str(part.date.min()),
                        "end": str(part.date.max()),
                    }
                    for name, part in parts.items()
                },
                "protocol": "Fixed-model rolling one-day-ahead holdout; past holdout outcomes become "
                "available as next-day lag inputs. Not a fixed-origin multi-step forecast.",
                "partial_final_day": str(daily.date.max()),
                "inference": "Unscored historical replay for final source date, withheld because it may be partial.",
                "zero_days": "Zero recorded sales, not asserted zero latent demand.",
            },
            ctx.path("reports", "model_performance", "feature_contract.json"),
        ),
    ]
    return outputs


if __name__ == "__main__":
    stage_cli(16)
