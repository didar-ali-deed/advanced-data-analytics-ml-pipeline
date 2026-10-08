"""Small synthetic fixtures are exclusively for software tests, never business findings."""

from pathlib import Path

import pandas as pd
import pytest

from utils.config_loader import load_config


@pytest.fixture
def root():
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def ctx(root):
    return load_config(root)


@pytest.fixture
def schema(ctx):
    return ctx.read_yaml("data_schema.yaml")


@pytest.fixture
def source():
    return pd.DataFrame(
        {
            "Invoice": ["100", "100", "C101", "102", "103", "104"],
            "StockCode": ["001", "002", "001", "003", "004", "005"],
            "Description": [" First  item ", "SECOND", "FIRST", None, "FREE", "BAD PRICE"],
            "Quantity": [2, 3, -1, 4, 1, 1],
            "InvoiceDate": pd.to_datetime(["2010-01-01 10:00"] * 3 + ["2010-01-03 00:00"] * 3),
            "Price": [10.0, 5.0, 10.0, 2.0, 0.0, -2.0],
            "Customer ID": ["00001", "00001", "00001", None, "00002", "00003"],
            "Country": ["United Kingdom"] * 5 + ["Germany"],
            "source_sheet": ["test"] * 6,
            "source_row": range(2, 8),
            "line_id": ["test:" + str(i) for i in range(2, 8)],
        }
    )


@pytest.fixture
def daily():
    dates = pd.date_range("2010-01-01", periods=150)
    sales = pd.Series(range(150), dtype=float) + 100
    return pd.DataFrame(
        {"date": dates, "gross_sales": sales, "orders": (sales % 11 + 1).astype(int)}
    )
