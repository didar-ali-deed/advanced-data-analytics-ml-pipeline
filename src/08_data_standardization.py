"""Stage 08: standardize types and names without unsupported currency conversions."""

from utils.data_loader import read_frame, save_frame, write_json
from utils.preprocessing import COLUMN_MAP, standardize
from utils.runner import stage_cli


def run(ctx):
    """Record every semantic mapping and timestamp/currency assumption."""
    frame = read_frame(ctx.path("data", "cleaned", "transactions.parquet"))
    normalized = standardize(frame)
    return [
        save_frame(normalized, ctx.path("data", "interim", "standardized.parquet")),
        write_json(
            {
                "columns": COLUMN_MAP,
                "currency": "GBP; no conversion",
                "timestamps": "Source-local naive datetime. Source does not document timezone.",
                "identifiers": "Strings; trim whitespace and numeric .0 suffix; retain leading zeros.",
                "country": "Whitespace cleanup only; no undocumented category harmonization.",
                "boolean": "Derived flags from explicit business rules, stored as Boolean.",
            },
            ctx.path("reports", "data_quality", "standardization.json"),
        ),
    ]


if __name__ == "__main__":
    stage_cli(8)
