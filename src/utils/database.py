"""SQLite connections and atomic bulk loading with enforced constraints."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from utils.data_validator import assert_primary_key


@contextmanager
def connect(path: Path) -> Iterator[sqlite3.Connection]:
    """Commit or roll back transactions and always close Windows file handles."""
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys = ON")
    try:
        with con:
            yield con
    finally:
        con.close()


def load_database(tables: dict[str, pd.DataFrame], destination: Path, sql_dir: Path) -> dict:
    """Load into a new constrained database and publish only after reconciliation."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".building.sqlite")
    if temporary.exists():
        temporary.unlink()
    counts = {}
    with connect(temporary) as con:
        con.executescript((sql_dir / "01_schema.sql").read_text(encoding="utf-8"))
        for name in ["dim_product", "dim_customer", "dim_country", "dim_date", "fact_sales"]:
            frame = tables[name].copy()
            if name == "fact_sales":
                assert_primary_key(frame, "line_id")
                frame["invoice_date"] = frame["invoice_date"].astype(str)
            frame = frame.astype(object).where(pd.notna(frame), None)
            columns = ", ".join(f'"{c}"' for c in frame.columns)
            placeholders = ", ".join("?" for _ in frame.columns)
            con.executemany(
                f'INSERT INTO "{name}" ({columns}) VALUES ({placeholders})',
                frame.itertuples(index=False, name=None),
            )
            count = con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
            if count != len(frame):
                raise ValueError(f"Database row mismatch in {name}")
            counts[name] = count
        if con.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("Database referential integrity failed")
        con.executescript((sql_dir / "05_reporting_views.sql").read_text(encoding="utf-8"))
    temporary.replace(destination)
    return counts
