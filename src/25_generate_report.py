"""Stage 25: compose a final report exclusively from produced analysis artifacts."""

import pandas as pd

from utils.data_loader import read_frame, read_json, write_json, write_text
from utils.runner import stage_cli


def run(ctx):
    """Generate a linked Markdown deliverable and combined visualization manifest."""
    quality = read_json(ctx.path("reports", "data_quality", "cleaning_log.json"))
    source = read_json(ctx.path("data", "raw", "provenance.json"))
    integration = read_json(ctx.path("reports", "data_quality", "integration.json"))
    metrics = read_json(ctx.path("models", "evaluation", "holdout_metrics.json"))
    contract = read_json(ctx.path("reports", "model_performance", "feature_contract.json"))
    tuning = read_json(ctx.path("models", "evaluation", "tuning_summary.json"))
    answers = read_json(ctx.path("reports", "business_insights", "sql_answers.json"))
    eda = read_json(ctx.path("reports", "exploratory", "eda.json"))
    comparison = read_frame(ctx.path("reports", "model_performance", "candidate_comparison.csv"))
    importance = read_frame(ctx.path("models", "evaluation", "permutation_importance.csv"))
    charts = []
    for stage in [4, 6, 15, 20, 21]:
        charts.extend(read_json(ctx.path("reports", "exploratory", f"charts_{stage:02d}.json")))
    overview = next(a for a in answers if a["id"] == "overview")
    country = next(a for a in answers if a["id"] == "country")
    stat_md = ctx.path("reports", "statistical", "statistics.md").read_text(encoding="utf-8")
    report = (
        f"# {ctx.config['project']}: final analytical report\n\n"
        "## Executive summary\n\n"
        f"{overview['interpretation']} {country['interpretation']}\n\n"
        f"Validated {quality['original_rows']:,} source lines; retained {quality['accepted_rows']:,}; "
        f"quarantined {quality['quarantined_rows']:,}. "
        f"Selected forecast model: **{metrics['selected_model']}**.\n\n"
        "## Sources and dataset\n\n"
        f"[Online Retail II]({source['documentation']}), {source['author']}, "
        f"{source['provider']}; {source['license']}; DOI {source['doi']}. "
        f"Retrieved {source['retrieved_utc']}. Archive SHA-256: `{source['archive_sha256']}`. "
        "Original Excel sheets are preserved. Dimensions are derived from this single source.\n\n"
        "## Business objectives\n\n"
        "Describe sales and cancellation exposure, diagnose geographic/product/customer concentration, "
        "quantify data-quality sensitivity, and evaluate next-day recorded-sales prediction. "
        "The project answers 22 SQL business questions plus statistical and predictive questions.\n\n"
        "## Data quality and cleaning\n\n"
        + pd.Series(
            {
                k: quality[k]
                for k in [
                    "original_rows",
                    "accepted_rows",
                    "quarantined_rows",
                    "unknown_customers",
                    "ambiguous_duplicate_rows_retained",
                ]
            },
            name="records",
        )
        .to_frame()
        .to_markdown()
        + "\n\nImpossible values are quarantined with reasons. Negative quantities and cancellations "
        "remain. Exact cross-sheet overlap copies are quarantined using original-field equality "
        "and per-sheet multiplicity. Ambiguous within-sheet repeated lines remain; sensitivity "
        "is separately reported. Missing customer IDs are UNKNOWN, never fabricated. Raw files remain immutable.\n\n"
        "## Analytical methodology and relational reconciliation\n\n"
        "Gross sales use positive quantity and price outside cancellation invoices; signed value includes "
        "adjustments and is not profit. All amounts remain GBP. Dates retain undocumented source-local "
        "timezone semantics. Calendar gaps mean zero observed sales, not known closure. "
        f"Integrated {integration['output_rows']:,} fact rows with {integration['orphan_rows']} orphans. "
        "SQLite enforces primary/foreign keys; SQL uses windows, CTEs and comparable-period filters.\n\n"
        "## SQL findings\n\n"
    )
    for answer in answers:
        report += (
            f"### {answer['question']}\n\n{answer['interpretation']}\n\n"
            f"Action to evaluate: {answer['potential_action']} "
            f"[Complete result](../../{answer['output']}).\n\n"
        )
    report += (
        "## Exploratory findings\n\n"
        f"Mean recorded calendar-day sales: GBP {eda['mean_daily_gross_sales']:,.2f}. "
        f"Dates with zero positive sales: {eda['zero_sales_days']}. "
        f"Daily autocorrelations: `{eda['daily_autocorrelation']}`. "
        "The final source day and final month may be partial.\n\n"
        "## Statistical findings\n\n" + stat_md.replace("# Statistical analysis\n\n", "") + "\n\n"
        "## Machine learning methodology\n\n"
        f"{contract['target']}. {contract['prediction_time']}. {contract['protocol']}\n\n"
        + pd.DataFrame(contract["split"]).T.to_markdown()
        + "\n\nPreprocessing, category encoding, scaling and variance selection fit within training "
        "folds. Candidate selection and tuning use validation MAE; final refit combines train and validation "
        "only. Features exclude same-day sales/orders and post-event transaction details.\n\n"
        "## Candidate comparison (validation, not independent test)\n\n"
        + comparison.to_markdown(index=False)
        + f"\n\nSearch winner parameters: `{tuning['best_parameters']}`. "
        f"Frozen model: **{tuning['selected_model']}**.\n\n"
        "## Independent chronological holdout\n\n"
        + pd.DataFrame(metrics["metrics"]).T.to_markdown()
        + "\n\nMAPE is omitted because zero-sales days make it inappropriate. "
        "WAPE uses total absolute error divided by total observed gross sales. "
        "Performance is conditional on daily updates of observed lag inputs.\n\n"
        "## Explainability\n\n"
        + importance.head(8).to_markdown(index=False)
        + "\n\nPermutation MAE changes are post-evaluation sensitivities. Correlated lags, temporal "
        "dependence and unrealistic shuffled combinations prevent causal or directional conclusions.\n\n"
        "## Visualization gallery\n\n"
    )
    for chart in charts:
        report += f"### {chart['title']}\n\n![{chart['title']}](../../{chart['path']})\n\n{chart['interpretation']}\n\n"
    report += (
        "## Business recommendations\n\n"
        "Resolve customer identifier gaps, review ambiguous duplicates with source owners, investigate "
        "high-contribution markets/products, and validate cancellation workflows. Use the forecast only "
        "after contemporary shadow testing against the seasonal baseline. "
        "[Evidence and individual actions](../business_insights/insights.md).\n\n"
        "## Power BI handoff\n\n"
        "The exports include fact_sales, four dimensions, and forecast_evaluation with validated keys. "
        "[Import instructions](../../powerbi/power_query_steps.md) and "
        "[DAX measures](../../powerbi/dax_measures.md) describe the manual Desktop build. "
        "No .pbix file has been generated or validated.\n\n"
        "## Limitations and future improvements\n\n"
        "Single historical retailer; anonymous customers; uncertain source duplicate identity; no profit, "
        "inventory, marketing, weather, or holiday-calendar enrichment; service codes included; partial final "
        "day; no causal design; correlated observations; limited daily training history; no calibrated "
        "forecast intervals. Obtain contemporary source line IDs and operations calendars, test multi-year "
        "rolling origins, and evaluate conditional uncertainty before deployment.\n\n"
        "## Reproducibility\n\n"
        "```powershell\npython -m venv .venv\n"
        ".\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt\n"
        ".\\.venv\\Scripts\\python.exe -m ruff check .\n"
        ".\\.venv\\Scripts\\python.exe -m pytest\n"
        ".\\.venv\\Scripts\\python.exe main.py --all\n```\n\n"
        "Checkpoint digests cover source code, configuration, SQL, runtime dependencies, dependency "
        "manifests and artifact bytes. Changed dependencies force rebuilding from the earliest affected "
        "stage. Use --force to rerun selected stages. Acquisition reuses verified immutable raw files."
    )
    return [
        write_json(charts, ctx.path("visualizations", "manifest.json")),
        write_text(report, ctx.path("reports", "final", "analysis_report.md")),
    ]


if __name__ == "__main__":
    stage_cli(25)
