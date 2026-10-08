"""Stage 22: schema-validated batch inference using the saved preprocessing pipeline."""

import joblib
import pandas as pd

from utils.data_loader import read_frame, save_frame, sha256, write_json
from utils.data_validator import validate_inference
from utils.modeling import predict
from utils.preprocessing import FEATURES
from utils.runner import stage_cli


def run(ctx):
    """Forecast supplied engineered rows or an explicitly labeled historical replay."""
    input_path = ctx.prediction_input or ctx.path("data", "features", "inference_input.csv")
    data = read_frame(input_path)
    validate_inference(data, FEATURES)
    if "date" not in data or pd.to_datetime(data["date"], errors="coerce").isna().any():
        raise ValueError("Inference requires valid target dates in the date column")
    dates = pd.to_datetime(data["date"])
    if dates.duplicated().any():
        raise ValueError("Duplicate prediction dates are not allowed")
    model_path = ctx.path("models", "trained", "final_model.joblib")
    model = joblib.load(model_path)
    output = pd.DataFrame({"date": dates, "predicted_gross_sales_gbp": predict(model, data)})
    output["prediction_kind"] = (
        "user_supplied_batch" if ctx.prediction_input else "unscored_historical_replay"
    )
    return [
        save_frame(output, ctx.path("models", "predictions", "batch_predictions.csv")),
        write_json(
            {
                "input_path": str(input_path),
                "input_sha256": sha256(input_path),
                "model_sha256": sha256(model_path),
                "rows": len(output),
                "uncertainty": "No interval: no calibrated uncertainty model was trained.",
                "availability": "Caller must ensure every lag/rolling value uses only completed days before date.",
                "default": "Replay on the potentially partial final source date; no validated future result claimed.",
            },
            ctx.path("models", "predictions", "prediction_manifest.json"),
        ),
    ]


if __name__ == "__main__":
    stage_cli(22)
