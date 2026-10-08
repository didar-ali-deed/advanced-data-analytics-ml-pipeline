"""Console logs plus machine-readable execution events."""

import logging.config

import yaml


def configure_logging(root):
    """Apply the checked-in logging configuration."""
    path = root / "config/logging.yaml"
    logging.config.dictConfig(yaml.safe_load(path.read_text(encoding="utf-8")))
