"""Offline integration and checkpoint invalidation, with clearly synthetic fixtures."""

import shutil
import zipfile

import pandas as pd
import pytest

from utils.config_loader import load_config
from utils.data_loader import read_json, sha256, write_json
from utils.runner import Runner


@pytest.fixture
def miniature_project(tmp_path, root):
    project = tmp_path / "project"
    project.mkdir()
    for directory in ["src", "config", "sql"]:
        shutil.copytree(
            root / directory, project / directory, ignore=shutil.ignore_patterns("__pycache__")
        )
    for filename in ["main.py", "requirements.txt", "pyproject.toml"]:
        shutil.copy2(root / filename, project / filename)
    ctx = load_config(project)
    ctx.config["analysis"].update(bootstrap_repetitions=20, sample_rows=200, chart_dpi=50)
    ctx.config["model"].update(
        cv_splits=2, search_iterations=1, n_jobs=1, min_training_days=30, permutation_repeats=2
    )
    raw = ctx.path("data", "raw")
    raw.mkdir(parents=True)
    rows = []
    for day, date in enumerate(pd.date_range("2010-01-01", periods=170)):
        for person in range(30):
            rows.append(
                {
                    "Invoice": str(day * 100 + person),
                    "StockCode": f"P{person % 3}",
                    "Description": f"TEST FIXTURE PRODUCT {person % 3}",
                    "Quantity": 1 + (day + person) % 8,
                    "InvoiceDate": date + pd.Timedelta(hours=10),
                    "Price": float(2 + person % 5),
                    "Customer ID": str(10000 + person),
                    "Country": "United Kingdom" if person < 15 else "Germany",
                }
            )
    workbook = tmp_path / ctx.config["source"]["workbook"]
    pd.DataFrame(rows).to_excel(workbook, index=False, sheet_name="TEST_ONLY")
    archive = raw / ctx.config["source"]["archive"]
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.write(workbook, arcname=workbook.name)
    write_json(
        {
            **ctx.config["source"],
            "archive_sha256": sha256(archive),
            "retrieved_utc": "TEST FIXTURE; not a production retrieval",
            "bytes": archive.stat().st_size,
        },
        raw / "provenance.json",
    )
    return ctx


def test_missing_dependency_has_actionable_error(miniature_project):
    with pytest.raises(RuntimeError, match="needs a current stage"):
        Runner(miniature_project).execute([3])


def test_all_25_stages_offline_and_checkpoint_integrity(miniature_project):
    ctx = miniature_project
    Runner(ctx).execute(range(1, 26))
    final = ctx.path("reports", "final", "analysis_report.md")
    assert final.exists()
    assert len(read_json(ctx.path("reports", "business_insights", "sql_answers.json"))) == 22
    assert (
        read_json(ctx.path("data", "powerbi", "export_manifest.json"))["foreign_key_violations"]
        == 0
    )
    metrics = read_json(ctx.path("models", "evaluation", "holdout_metrics.json"))
    assert metrics["selection_independent_of_test"]
    assert metrics["metrics"]["selected"]["n"] > 0
    manifest = ctx.root / ".pipeline/25.json"
    previous = manifest.read_bytes()
    Runner(ctx).execute(range(1, 26))
    assert manifest.read_bytes() == previous  # A genuine content-verified no-op.
    output = ctx.path("models", "predictions", "batch_predictions.csv")
    output.write_text("corrupted output", encoding="utf-8")
    assert not Runner(ctx).valid(25)
    source = ctx.root / "src/01_download_data.py"
    source.write_text(source.read_text(encoding="utf-8") + "\n# changed source\n", encoding="utf-8")
    assert not Runner(ctx).valid(1)
