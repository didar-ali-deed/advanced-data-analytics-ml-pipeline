"""Stage 24: validate and export the relational model for Power BI Desktop."""

import pandas as pd

from utils.data_loader import read_frame, save_frame, sha256, write_json, write_text
from utils.data_validator import assert_foreign_key, assert_primary_key
from utils.runner import stage_cli


def run(ctx):
    """Export explicit dimensions, a fact table, daily model errors and a data dictionary."""
    names = ["dim_product", "dim_customer", "dim_country", "dim_date", "fact_sales"]
    tables = {name: read_frame(ctx.path("data", "processed", name + ".parquet")) for name in names}
    fact = tables["fact_sales"]
    assert_primary_key(fact, "line_id")
    for name, key in [
        ("dim_product", "product_id"),
        ("dim_customer", "customer_id"),
        ("dim_country", "country_id"),
        ("dim_date", "date"),
    ]:
        assert_foreign_key(fact, tables[name], key)
    tables["forecast_evaluation"] = read_frame(
        ctx.path("models", "evaluation", "holdout_predictions.csv")
    )
    assert_primary_key(tables["forecast_evaluation"], "date")
    assert_foreign_key(tables["forecast_evaluation"], tables["dim_date"], "date")
    outputs, manifest, dictionary = [], {}, []
    for name, frame in tables.items():
        output = save_frame(frame, ctx.path("data", "powerbi", name + ".csv"))
        outputs.append(output)
        manifest[name] = {
            "rows": len(frame),
            "sha256": sha256(output),
            "path": output.relative_to(ctx.root).as_posix(),
        }
        dictionary.extend(
            {
                "table": name,
                "column": c,
                "pandas_dtype": str(frame[c].dtype),
                "null_count": int(frame[c].isna().sum()),
            }
            for c in frame
        )
    outputs.extend(
        [
            write_json(
                {
                    "tables": manifest,
                    "foreign_key_violations": 0,
                    "date_parse": "ISO YYYY-MM-DD",
                    "encoding": "UTF-8",
                },
                ctx.path("data", "powerbi", "export_manifest.json"),
            ),
            save_frame(
                pd.DataFrame(dictionary), ctx.path("data", "powerbi", "data_dictionary.csv")
            ),
            write_text(
                "# Power BI export validation\n\nAll fact keys matched unique, non-null dimensions. "
                "Forecast evaluation has one row per holdout date. No .pbix file is generated; "
                "follow powerbi/power_query_steps.md in Power BI Desktop.\n\n"
                + pd.DataFrame(manifest).T[["rows", "sha256"]].to_markdown(),
                ctx.path("reports", "data_quality", "powerbi_validation.md"),
            ),
        ]
    )
    return outputs


if __name__ == "__main__":
    stage_cli(24)
