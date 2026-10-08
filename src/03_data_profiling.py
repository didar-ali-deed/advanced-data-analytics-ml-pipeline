"""Stage 03: establish an auditable baseline profile."""

from utils.data_loader import read_frame, save_frame, write_json
from utils.data_quality import missing_summary, profile
from utils.runner import stage_cli


def run(ctx):
    """Profile all validated rows and persist numerical and column summaries."""
    frame = read_frame(ctx.path("data", "validated", "transactions.parquet"))
    return [
        write_json(profile(frame), ctx.path("reports", "data_quality", "profile_raw.json")),
        save_frame(
            missing_summary(frame), ctx.path("reports", "data_quality", "profile_columns.csv")
        ),
        save_frame(
            frame.select_dtypes("number").describe().reset_index(),
            ctx.path("reports", "data_quality", "profile_numeric.csv"),
        ),
    ]


if __name__ == "__main__":
    stage_cli(3)
