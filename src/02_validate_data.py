"""Stage 02: validate the source workbook while retaining all row-level issues."""

import pandas as pd

from utils.data_loader import save_frame, write_json, write_text
from utils.data_validator import validate_source
from utils.runner import stage_cli


def run(ctx):
    """Read both sheets and assign immutable source-sheet/Excel-row lineage keys."""
    path = ctx.path("data", "raw", ctx.config["source"]["workbook"])
    schema = ctx.read_yaml("data_schema.yaml")
    pieces, reports = [], {}
    with pd.ExcelFile(path) as workbook:
        for sheet in workbook.sheet_names:
            frame = pd.read_excel(
                workbook,
                sheet_name=sheet,
                dtype={
                    "Invoice": "string",
                    "StockCode": "string",
                    "Customer ID": "string",
                    "Description": "string",
                    "Country": "string",
                },
            )
            frame["source_sheet"] = sheet
            frame["source_row"] = range(2, len(frame) + 2)
            frame["line_id"] = sheet + ":" + frame["source_row"].astype(str)
            reports[sheet] = validate_source(frame, schema)
            pieces.append(frame)
    outputs = [
        write_json(reports, ctx.path("reports", "data_quality", "validation.json")),
        write_text(
            "# Source validation\n\n"
            + "\n\n".join(
                f"## {name}\n\nRows: {r['rows']:,}\n\n"
                + pd.Series(r["issues"], name="flagged_rows").to_frame().to_markdown()
                + "\n\nBlocking: "
                + str(r["blocking"])
                for name, r in reports.items()
            ),
            ctx.path("reports", "data_quality", "validation.md"),
        ),
    ]
    if any(report["blocking"] for report in reports.values()):
        raise ValueError("Source schema validation failed; inspect validation.json")
    combined = pd.concat(pieces, ignore_index=True)
    outputs.append(save_frame(combined, ctx.path("data", "validated", "transactions.parquet")))
    return outputs


if __name__ == "__main__":
    stage_cli(2)
