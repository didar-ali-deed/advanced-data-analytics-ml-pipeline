"""Stage 05: distinguish repeated invoice lines from invalid keys."""

from utils.data_loader import read_frame, save_frame, write_json, write_text
from utils.data_quality import duplicate_summary
from utils.runner import stage_cli


def run(ctx):
    """Report exact business repeats and near repeats, retaining uncertain evidence."""
    frame = read_frame(ctx.path("data", "validated", "transactions.parquet"))
    columns = ctx.read_yaml("data_schema.yaml")["required"]
    summary = duplicate_summary(frame, columns)
    near_keys = ["Invoice", "StockCode", "Quantity", "Price", "Customer ID"]
    summary["near_repeat_rows"] = int(frame.duplicated(near_keys, keep=False).sum())
    examples = frame.loc[frame.duplicated(columns, keep=False)].head(200)
    return [
        write_json(summary, ctx.path("reports", "data_quality", "duplicates.json")),
        save_frame(examples, ctx.path("reports", "data_quality", "duplicate_examples.csv")),
        write_text(
            "# Duplicate review\n\n" + str(summary) + "\n\nInvoice IDs are one-to-many, "
            "not line primary keys. Identical lines may represent repeated product entries; "
            "without an authoritative line ID there is no evidence to delete within-sheet repeats. "
            "Stage 07 separately reconciles exact cross-sheet copies in the overlapping source "
            "date windows, retaining maximum per-sheet multiplicity and quarantining extra copies. "
            "Near-repeat groups ignore description and timestamp and are review candidates only. "
            "A separate sensitivity query measures the effect of deduplicating business rows.",
            ctx.path("reports", "data_quality", "duplicates.md"),
        ),
    ]


if __name__ == "__main__":
    stage_cli(5)
