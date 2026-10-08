"""Command-line entry point for all 25 stages."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from utils.runner import cli  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(cli())
