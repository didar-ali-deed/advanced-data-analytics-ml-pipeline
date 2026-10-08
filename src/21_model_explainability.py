"""Stage 21: post-evaluation permutation diagnostics on frozen holdout predictions."""

import joblib
import pandas as pd
from sklearn.inspection import permutation_importance

from utils.data_loader import save_frame, write_text
from utils.modeling import nonnegative_mae_score, splits
from utils.preprocessing import FEATURES
from utils.runner import stage_cli
from utils.visualization import Charts, bar_figure


def run(ctx):
    """Measure model sensitivity; do not use test importance for model reselection."""
    test = splits(ctx)["test"]
    model = joblib.load(ctx.path("models", "trained", "final_model.joblib"))
    result = permutation_importance(
        model,
        test[FEATURES],
        test.target,
        scoring=nonnegative_mae_score,
        n_repeats=ctx.config["model"]["permutation_repeats"],
        random_state=ctx.config["seed"],
        n_jobs=ctx.config["model"]["n_jobs"],
    )
    frame = pd.DataFrame(
        {
            "feature": FEATURES,
            "mae_increase_gbp": result.importances_mean,
            "repeat_sd_gbp": result.importances_std,
        }
    ).sort_values("mae_increase_gbp", ascending=False)
    charts = Charts(ctx, 21)
    charts.save(
        bar_figure(
            frame.set_index("feature").mae_increase_gbp,
            "Increase in MAE after permutation (GBP)",
            "Feature",
        ),
        "machine_learning",
        "permutation_importance",
        "Frozen-model permutation sensitivity",
        "Which inputs does this fitted model rely on?",
        f"Largest observed sensitivity: {frame.iloc[0].feature}; "
        "correlated lags and calendar dependencies make this diagnostic non-causal.",
    )
    return [
        save_frame(frame, ctx.path("models", "evaluation", "permutation_importance.csv")),
        write_text(
            "# Explainability limits\n\nPermutation is a post-evaluation diagnostic; the model is "
            "already frozen. Shuffling disrupts time/feature dependence and may create unrealistic "
            "combinations. Correlated lags can share or obscure importance. Repeat standard deviation "
            "is permutation variability, not a population confidence interval. Importance does not "
            "establish direction or causation. SHAP/PDP are omitted because temporal lag dependence "
            "would require additional conditional-background assumptions. Historical wholesale mix, "
            "missing identities and a single retailer limit generalization.",
            ctx.path("reports", "model_performance", "explainability.md"),
        ),
    ] + charts.finish()


if __name__ == "__main__":
    stage_cli(21)
