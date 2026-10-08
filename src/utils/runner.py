"""Dependency-aware execution, content checkpoints, and failure reporting."""

import argparse
import hashlib
import importlib.metadata
import json
import logging
import runpy
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from utils.config_loader import load_config
from utils.data_loader import read_json, sha256, write_json
from utils.logger import configure_logging

NAMES = [
    "download_data",
    "validate_data",
    "data_profiling",
    "missing_value_analysis",
    "duplicate_analysis",
    "outlier_analysis",
    "data_cleaning",
    "data_standardization",
    "data_transformation",
    "data_integration",
    "database_creation",
    "sql_analysis",
    "exploratory_analysis",
    "statistical_analysis",
    "data_visualization",
    "feature_engineering",
    "feature_selection",
    "model_training",
    "hyperparameter_tuning",
    "model_evaluation",
    "model_explainability",
    "prediction",
    "business_insights",
    "powerbi_export",
    "generate_report",
]
# Conservative linear dependencies make stage ranges unambiguous and auditable.
DEPENDENCIES = {number: [number - 1] if number > 1 else [] for number in range(1, 26)}
LOGGER = logging.getLogger("pipeline")


def digest(value) -> str:
    """Hash canonical JSON metadata."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def source_fingerprint(ctx) -> str:
    """Include code, config, SQL, dependencies, and the active Python runtime."""
    paths = [ctx.root / "main.py", ctx.root / "requirements.txt", ctx.root / "pyproject.toml"]
    for area, pattern in [("src", "*.py"), ("config", "*.yaml"), ("sql", "*.sql")]:
        paths.extend(sorted((ctx.root / area).rglob(pattern)))
    versions = {
        name: importlib.metadata.version(name)
        for name in [
            "numpy",
            "pandas",
            "scipy",
            "scikit-learn",
            "pyarrow",
            "matplotlib",
            "seaborn",
            "joblib",
            "openpyxl",
            "PyYAML",
            "requests",
        ]
    }
    return digest(
        {
            "files": {str(p.relative_to(ctx.root)): sha256(p) for p in paths},
            "config": ctx.config,
            "versions": versions,
            "python": sys.version,
        }
    )


class Runner:
    """Execute stages only when required checkpoints and output hashes are valid."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.base = source_fingerprint(ctx)
        self.cache = {}

    def manifest_path(self, number):
        return self.ctx.root / ".pipeline" / f"{number:02d}.json"

    def fingerprint(self, number):
        dependencies = {
            str(dep): sha256(self.manifest_path(dep)) if self.manifest_path(dep).exists() else None
            for dep in DEPENDENCIES[number]
        }
        inference = None
        if number == 22 and self.ctx.prediction_input:
            inference = sha256(self.ctx.prediction_input)
        return digest({"source": self.base, "deps": dependencies, "inference": inference})

    def valid(self, number):
        """Recursively reject missing, modified, or stale upstream artifacts."""
        if number in self.cache:
            return self.cache[number]
        path = self.manifest_path(number)
        valid = False
        if path.exists() and all(self.valid(d) for d in DEPENDENCIES[number]):
            data = read_json(path)
            valid = data.get("fingerprint") == self.fingerprint(number)
            if valid:
                valid = all(
                    (self.ctx.root / p).is_file() and sha256(self.ctx.root / p) == checksum
                    for p, checksum in data["outputs"].items()
                )
        self.cache[number] = valid
        return valid

    def execute(self, selected, force=False):
        """Stop on the first failed stage; never mark partial outputs as successful."""
        for number in selected:
            for dep in DEPENDENCIES[number]:
                if not self.valid(dep):
                    raise RuntimeError(
                        f"Stage {number:02d} needs a current stage {dep:02d} checkpoint. "
                        f"Run python main.py --from-stage 1 --to-stage {number} to rebuild."
                    )
            if not force and self.valid(number):
                LOGGER.info("stage=%02d status=skipped reason=verified_checkpoint", number)
                continue
            manifest = self.manifest_path(number)
            manifest.unlink(missing_ok=True)
            started = time.perf_counter()
            script = self.ctx.root / "src" / f"{number:02d}_{NAMES[number - 1]}.py"
            LOGGER.info("stage=%02d status=started name=%s", number, NAMES[number - 1])
            try:
                outputs = runpy.run_path(str(script))["run"](self.ctx)
                if not outputs or any(not p.is_file() for p in outputs):
                    raise RuntimeError("Stage did not produce all declared artifacts")
                document = {
                    "stage": number,
                    "name": NAMES[number - 1],
                    "status": "success",
                    "completed_utc": datetime.now(timezone.utc).isoformat(),
                    "seconds": time.perf_counter() - started,
                    "fingerprint": self.fingerprint(number),
                    "outputs": {
                        p.relative_to(self.ctx.root).as_posix(): sha256(p) for p in outputs
                    },
                }
                write_json(document, manifest)
                self.cache = {k: v for k, v in self.cache.items() if k < number}
                self.cache[number] = True
                LOGGER.info("stage=%02d status=success seconds=%.2f", number, document["seconds"])
            except Exception as exc:
                self.cache.clear()
                write_json(
                    {
                        "stage": number,
                        "name": NAMES[number - 1],
                        "error": str(exc),
                        "failed_utc": datetime.now(timezone.utc).isoformat(),
                        "seconds": time.perf_counter() - started,
                    },
                    self.ctx.root / ".pipeline/last_failure.json",
                )
                LOGGER.exception("stage=%02d status=failed", number)
                raise RuntimeError(
                    f"Stage {number:02d} ({NAMES[number - 1]}) failed: {exc}"
                ) from exc


def cli(argv=None, fixed_stage=None):
    """Parse complete, individual, and contiguous-range execution modes."""
    parser = argparse.ArgumentParser(
        description="Run the audited 25-stage retail analytics pipeline."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Run or resume all stages")
    group.add_argument("--stage", type=int, choices=range(1, 26), help="Run one stage")
    parser.add_argument("--from-stage", type=int, choices=range(1, 26))
    parser.add_argument("--to-stage", type=int, choices=range(1, 26))
    parser.add_argument("--force", action="store_true", help="Rerun selected stages")
    parser.add_argument("--config", type=Path, help="Alternate YAML configuration")
    parser.add_argument("--prediction-input", type=Path, help="Engineered-feature CSV for stage 22")
    args = parser.parse_args(argv)
    if (args.all or args.stage) and (args.from_stage or args.to_stage):
        parser.error("Use --all, --stage, or a stage range, not a combination")
    start, end = args.from_stage or 1, args.to_stage or 25
    if start > end:
        parser.error("--from-stage must not exceed --to-stage")
    selected = [fixed_stage or args.stage] if fixed_stage or args.stage else range(start, end + 1)
    root = Path(__file__).resolve().parents[2]
    ctx = load_config(root, args.config)
    if args.prediction_input:
        ctx.prediction_input = args.prediction_input.resolve()
    elif ctx.config["prediction"]["input"]:
        ctx.prediction_input = root / ctx.config["prediction"]["input"]
    configure_logging(root)
    try:
        Runner(ctx).execute(selected, args.force)
    except Exception as exc:
        LOGGER.error("%s", exc)
        return 1
    return 0


def stage_cli(number: int):
    """Provide the same safe orchestration for directly executed numbered scripts."""
    raise SystemExit(cli(fixed_stage=number))
