"""Stage 07: controlled cleaning, quarantine, and before/after reconciliation."""

from utils.data_loader import read_frame, save_frame, write_json
from utils.data_quality import profile
from utils.preprocessing import clean_transactions
from utils.runner import stage_cli


def run(ctx):
    """Apply documented deterministic rules while leaving source files immutable."""
    frame = read_frame(ctx.path("data", "validated", "transactions.parquet"))
    accepted, quarantine, log = clean_transactions(frame, ctx.read_yaml("data_schema.yaml"))
    return [
        save_frame(accepted, ctx.path("data", "cleaned", "transactions.parquet")),
        save_frame(quarantine, ctx.path("data", "interim", "quarantine.parquet")),
        write_json(log, ctx.path("reports", "data_quality", "cleaning_log.json")),
        write_json(profile(accepted), ctx.path("reports", "data_quality", "profile_cleaned.json")),
        write_json(
            {"before": profile(frame)["missing"], "after": profile(accepted)["missing"]},
            ctx.path("reports", "data_quality", "profile_comparison.json"),
        ),
    ]


if __name__ == "__main__":
    stage_cli(7)
