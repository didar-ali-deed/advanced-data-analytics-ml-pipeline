"""Dimension grain, row multiplication prevention and real database constraints."""

import sqlite3

import pytest

from utils.database import connect, load_database
from utils.preprocessing import build_star, clean_transactions, standardize, transform
from utils.questions import load_queries


def test_star_preserves_counts_and_identifiers(source, schema):
    clean, _, _ = clean_transactions(source, schema)
    lines, _ = transform(standardize(clean))
    tables, report = build_star(lines)
    assert len(tables["fact_sales"]) == len(lines)
    assert report["orphan_rows"] == 0
    assert tables["dim_product"].product_id.is_unique
    assert "00001" in tables["dim_customer"].customer_id.tolist()


def test_sql_constraints_and_questions(source, schema, root, tmp_path):
    clean, _, _ = clean_transactions(source, schema)
    lines, _ = transform(standardize(clean))
    tables, _ = build_star(lines)
    destination = tmp_path / "test.sqlite"
    counts = load_database(tables, destination, root / "sql")
    assert counts["fact_sales"] == 5
    with connect(destination) as con:
        for query in load_queries(root / "sql").values():
            con.execute(query).fetchall()
        with pytest.raises(sqlite3.IntegrityError):
            con.execute("UPDATE fact_sales SET product_id = 'missing' WHERE line_id = 'test:2'")
        assert not con.execute("PRAGMA foreign_key_check").fetchall()
