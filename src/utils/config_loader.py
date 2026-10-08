"""Validated configuration and project-relative paths."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Context:
    """Paths and configuration passed explicitly to every stage."""

    root: Path
    config: dict[str, Any]
    prediction_input: Path | None = None

    def path(self, area: str, *parts: str) -> Path:
        """Resolve a configured artifact area, never a user-specific path."""
        return self.root / self.config["paths"].get(area, area) / Path(*parts)

    def read_yaml(self, name: str) -> dict:
        """Read a repository configuration resource."""
        return yaml.safe_load((self.root / "config" / name).read_text(encoding="utf-8"))


def load_config(root: Path, config_file: Path | None = None) -> Context:
    """Load a project config and reject invalid compute or split settings."""
    root = root.resolve()
    path = config_file or root / "config/config.yaml"
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    model = config["model"]
    if not 0 < model["train_fraction"] < 1:
        raise ValueError("train_fraction must be between zero and one")
    if not 0 < model["validation_fraction"] < 1 - model["train_fraction"]:
        raise ValueError("validation_fraction must leave a positive test fraction")
    if model["cv_splits"] < 2 or model["search_iterations"] < 1:
        raise ValueError("At least two CV splits and one search iteration are required")
    return Context(root, config)
