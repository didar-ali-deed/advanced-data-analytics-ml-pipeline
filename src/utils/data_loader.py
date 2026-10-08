"""Strict readers and atomic artifact writers."""

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def sha256(path: Path) -> str:
    """Compute a streaming content digest."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_frame(path: Path, **kwargs: Any) -> pd.DataFrame:
    """Read supported formats; decoding errors and empty files fail explicitly."""
    if not path.is_file():
        raise FileNotFoundError(f"Missing input: {path}")
    if path.suffix == ".parquet":
        frame = pd.read_parquet(path, **kwargs)
    elif path.suffix == ".csv":
        frame = pd.read_csv(path, encoding="utf-8", encoding_errors="strict", **kwargs)
    elif path.suffix in {".xlsx", ".xls"}:
        frame = pd.read_excel(path, **kwargs)
    elif path.suffix == ".json":
        frame = pd.read_json(path, **kwargs)
    else:
        raise ValueError(f"Unsupported table format: {path.suffix}")
    if frame.empty:
        raise ValueError(f"Input has no records: {path}")
    return frame


def save_frame(frame: pd.DataFrame, path: Path) -> Path:
    """Atomically save a table, retaining the caller's chosen format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.stem + ".tmp" + path.suffix)
    if path.suffix == ".parquet":
        frame.to_parquet(temp, index=False)
    elif path.suffix == ".csv":
        frame.to_csv(temp, index=False, encoding="utf-8")
    else:
        raise ValueError(f"Unsupported output format: {path.suffix}")
    temp.replace(path)
    return path


def json_safe(value: Any) -> Any:
    """Convert scientific scalars to interoperable JSON, mapping NaN to null."""
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return json_safe(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    return value


def write_json(value: Any, path: Path) -> Path:
    """Write strict JSON with no nonstandard NaN literals."""
    return write_text(json.dumps(json_safe(value), indent=2, allow_nan=False), path)


def read_json(path: Path) -> Any:
    """Load a UTF-8 JSON artifact."""
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(text: str, path: Path) -> Path:
    """Atomically write a UTF-8 text artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)
    return path
