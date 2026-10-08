"""Stage 04: examine missingness across fields, geography, and time."""

import matplotlib.pyplot as plt
import seaborn as sns

from utils.data_loader import read_frame, save_frame, write_text
from utils.data_quality import missing_summary
from utils.runner import stage_cli
from utils.visualization import Charts, bar_figure


def run(ctx):
    """Measure missingness; do not learn model imputations on these data."""
    frame = read_frame(ctx.path("data", "validated", "transactions.parquet"))
    summary = missing_summary(frame)
    by_country = (
        frame.assign(customer_missing=frame["Customer ID"].isna())
        .groupby("Country", dropna=False)["customer_missing"]
        .agg(["size", "mean"])
        .reset_index()
    )
    by_month = (
        frame.assign(
            month=frame["InvoiceDate"].dt.strftime("%Y-%m"),
            customer_missing=frame["Customer ID"].isna(),
        )
        .groupby("month")["customer_missing"]
        .agg(["size", "mean"])
        .reset_index()
    )
    outputs = [
        save_frame(summary, ctx.path("reports", "data_quality", "missingness.csv")),
        save_frame(by_country, ctx.path("reports", "data_quality", "missingness_country.csv")),
        save_frame(by_month, ctx.path("reports", "data_quality", "missingness_month.csv")),
        write_text(
            "# Missingness policy\n\nMissing customer identifiers remain UNKNOWN; do not invent "
            "customer assignments. Missing descriptions use UNKNOWN. Missing essential monetary, "
            "date, or product fields are quarantined. Descriptive aggregates retain anonymous sales. "
            "Predictive numeric median imputers and missing indicators fit within training folds only. "
            "No forward filling is justified for transaction identifiers. Country/month differences "
            "are diagnostics, not evidence of a specific missing-data mechanism.",
            ctx.path("reports", "data_quality", "missingness_strategy.md"),
        ),
    ]
    charts = Charts(ctx, 4)
    charts.save(
        bar_figure(summary.set_index("column")["missing_pct"], "Missing (%)", "Field"),
        "anomalies",
        "missing_bar",
        "Missing values by source field",
        "Which fields lack information?",
        f"Customer IDs are missing in {frame['Customer ID'].isna().mean():.1%} of source rows.",
    )
    sample = frame.sample(min(1000, len(frame)), random_state=ctx.config["seed"])
    fig, ax = plt.subplots(figsize=(11, 4))
    sns.heatmap(
        sample.isna().astype(int), cmap=["#EAF1F3", "#C45B60"], cbar=False, yticklabels=False, ax=ax
    )
    ax.set(xlabel="Source field", ylabel="Randomly sampled rows (not time ordered)")
    charts.save(
        fig,
        "anomalies",
        "missing_matrix",
        "Missingness across sampled source rows",
        "Do missing fields co-occur?",
        "Display shows a seeded sample; totals use all rows.",
    )
    flags = frame[["Description", "Customer ID", "Country"]].isna().astype(float)
    cooccurrence = flags.T.dot(flags) / len(frame) * 100
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cooccurrence, annot=True, fmt=".2f", cmap="Blues", cbar_kws={"label": "All rows (%)"}, ax=ax
    )
    charts.save(
        fig,
        "anomalies",
        "missing_heatmap",
        "Joint missingness as percentage of all rows",
        "Which fields are absent together?",
        "Cells use all source rows as the denominator.",
    )
    return outputs + charts.finish()


if __name__ == "__main__":
    stage_cli(4)
