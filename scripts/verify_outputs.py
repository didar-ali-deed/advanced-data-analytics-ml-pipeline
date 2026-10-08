"""Verify real pipeline outputs, relational reconciliation and report references."""

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from utils.config_loader import load_config  # noqa: E402
from utils.data_loader import read_json, write_json  # noqa: E402
from utils.database import connect  # noqa: E402
from utils.runner import NAMES, Runner  # noqa: E402


def verify() -> dict:
    """Reject missing/stale artifacts and inconsistent counts; print a compact audit."""
    ctx = load_config(ROOT)
    required = [
        "config/config.yaml",
        "config/data_schema.yaml",
        "config/logging.yaml",
        "sql/01_schema.sql",
        "sql/02_data_quality.sql",
        "sql/03_business_kpis.sql",
        "sql/04_advanced_analysis.sql",
        "sql/05_reporting_views.sql",
        "README.md",
        "LICENSE",
        "requirements.txt",
        "pyproject.toml",
        ".env.example",
        "powerbi/data_model.md",
        "powerbi/dax_measures.md",
        "powerbi/dashboard_design.md",
        "powerbi/power_query_steps.md",
        "docs/data_dictionary.md",
        "docs/data_sources.md",
        "docs/methodology.md",
        "docs/pipeline_architecture.md",
        "docs/business_questions.md",
        "docs/project_findings.md",
        "reports/final/analysis_report.md",
    ]
    required.extend(f"src/{number:02d}_{name}.py" for number, name in enumerate(NAMES, 1))
    for name in required:
        if not (ROOT / name).is_file():
            raise AssertionError(f"Required file absent: {name}")
    runner = Runner(ctx)
    if not runner.valid(25):
        raise AssertionError("Final checkpoint is stale or incomplete; run main.py --all")
    clean = read_json(ctx.path("reports", "data_quality", "cleaning_log.json"))
    assert clean["original_rows"] == clean["accepted_rows"] + clean["quarantined_rows"]
    with connect(ctx.path("data", "processed", "retail.sqlite")) as con:
        assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert not con.execute("PRAGMA foreign_key_check").fetchall()
        count, value = con.execute("SELECT COUNT(*), SUM(gross_sales) FROM fact_sales").fetchone()
        assert count == clean["accepted_rows"]
    answers = read_json(ctx.path("reports", "business_insights", "sql_answers.json"))
    assert len(answers) >= 20
    chart_manifest = read_json(ctx.path("visualizations", "manifest.json"))
    for chart in chart_manifest:
        assert (ROOT / chart["path"]).is_file()
        assert chart["title"] and chart["question"] and chart["interpretation"]
    exported = read_json(ctx.path("data", "powerbi", "export_manifest.json"))
    assert exported["foreign_key_violations"] == 0
    assert exported["tables"]["fact_sales"]["rows"] == count
    metrics = read_json(ctx.path("models", "evaluation", "holdout_metrics.json"))
    predictions = pd.read_csv(ctx.path("models", "predictions", "batch_predictions.csv"))
    assert predictions.predicted_gross_sales_gbp.notna().all()
    assert (predictions.predicted_gross_sales_gbp >= 0).all()
    broken_links = []
    for path in [ROOT / "README.md", ctx.path("reports", "final", "analysis_report.md")]:
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if target.startswith(("https://", "http://", "#")):
                continue
            if not (path.parent / target.split("#")[0]).exists():
                broken_links.append({"document": str(path.relative_to(ROOT)), "target": target})
    if broken_links:
        raise AssertionError(f"Broken deliverable links: {broken_links}")
    result = {
        "verified_stages": 25,
        "source_rows": clean["original_rows"],
        "accepted_rows": count,
        "quarantined_rows": clean["quarantined_rows"],
        "gross_sales_gbp": value,
        "sql_questions": len(answers),
        "charts": len(chart_manifest),
        "powerbi_tables": len(exported["tables"]),
        "selected_model": metrics["selected_model"],
        "holdout_metrics": metrics["metrics"],
        "broken_links": broken_links,
        "raw_sha256": read_json(ctx.path("data", "raw", "provenance.json"))["archive_sha256"],
    }
    write_json(result, ctx.path("reports", "final", "verification.json"))
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
