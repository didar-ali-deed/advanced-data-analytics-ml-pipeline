"""Stage 11: create and atomically publish a constrained SQLite database."""

from utils.data_loader import read_frame, write_json
from utils.database import load_database
from utils.runner import stage_cli


def run(ctx):
    """Load dimensions before facts and verify database integrity."""
    tables = {
        name: read_frame(ctx.path("data", "processed", name + ".parquet"))
        for name in ["dim_product", "dim_customer", "dim_country", "dim_date", "fact_sales"]
    }
    database = ctx.path("data", "processed", "retail.sqlite")
    counts = load_database(tables, database, ctx.root / "sql")
    return [
        database,
        write_json(counts, ctx.path("reports", "data_quality", "database_counts.json")),
    ]


if __name__ == "__main__":
    stage_cli(11)
