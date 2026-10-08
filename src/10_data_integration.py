"""Stage 10: derive and reconcile a relational star model."""

from utils.data_loader import read_frame, save_frame, write_json
from utils.preprocessing import build_star
from utils.runner import stage_cli


def run(ctx):
    """Validate all primary/foreign keys and preserve line totals through joins."""
    lines = read_frame(ctx.path("data", "processed", "lines.parquet"))
    tables, report = build_star(lines)
    return [
        save_frame(frame, ctx.path("data", "processed", name + ".parquet"))
        for name, frame in tables.items()
    ] + [write_json(report, ctx.path("reports", "data_quality", "integration.json"))]


if __name__ == "__main__":
    stage_cli(10)
