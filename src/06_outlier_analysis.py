"""Stage 06: flag extreme observations without deleting legitimate wholesale activity."""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from utils.data_loader import read_frame, save_frame, write_json
from utils.data_quality import outlier_flags
from utils.runner import stage_cli
from utils.visualization import Charts


def run(ctx):
    """Compare IQR, z-score, MAD, percentile and domain-rule anomaly flags."""
    frame = read_frame(ctx.path("data", "validated", "transactions.parquet"))
    summaries, flagged = [], pd.DataFrame({"line_id": frame["line_id"]})
    for column in ["Quantity", "Price"]:
        flags = outlier_flags(frame[column])
        for method in flags:
            summaries.append(
                {
                    "column": column,
                    "method": method,
                    "rows": int(flags[method].sum()),
                    "fraction": flags[method].mean(),
                }
            )
        flagged[column + "_iqr"] = flags["iqr"]
    flagged["negative_price"] = frame["Price"] < 0
    flagged["zero_price"] = frame["Price"].eq(0)
    segments = (
        frame.assign(quantity_iqr=flagged["Quantity_iqr"])
        .groupby("Country", dropna=False)["quantity_iqr"]
        .agg(["size", "mean"])
        .reset_index()
    )
    charts = Charts(ctx, 6)
    sample = frame.sample(
        min(len(frame), ctx.config["analysis"]["sample_rows"]), random_state=ctx.config["seed"]
    )
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for ax, column in zip(axes, ["Quantity", "Price"], strict=True):
        sns.boxplot(x=sample[column], ax=ax, color="#147D92")
        ax.set_xscale("symlog")
        ax.set_xlabel(
            column + (" (GBP, symmetric log)" if column == "Price" else " (symmetric log)")
        )
    charts.save(
        fig,
        "anomalies",
        "source_outliers",
        "Signed source quantities and prices",
        "How extreme are the recorded values?",
        "Statistical extremes remain; negative prices are separately quarantined. "
        "Isolation Forest is omitted because univariate rules are interpretable for these fields.",
    )
    return [
        save_frame(pd.DataFrame(summaries), ctx.path("reports", "data_quality", "outliers.csv")),
        save_frame(flagged, ctx.path("data", "interim", "outlier_flags.parquet")),
        save_frame(segments, ctx.path("reports", "data_quality", "outliers_country.csv")),
        write_json(
            {
                "policy": "Retain statistical extremes; quarantine impossible values only.",
                "mad_zero": "MAD flags disabled for a constant or zero-MAD variable.",
            },
            ctx.path("reports", "data_quality", "outlier_policy.json"),
        ),
    ] + charts.finish()


if __name__ == "__main__":
    stage_cli(6)
