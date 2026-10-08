"""Schema, key, encoding, inference and archive integrity edge cases."""

import zipfile

import numpy as np
import pandas as pd
import pytest

from utils.acquisition import safe_extract
from utils.data_loader import read_frame
from utils.data_validator import (
    assert_foreign_key,
    assert_primary_key,
    validate_inference,
    validate_source,
)


def test_missing_columns_and_empty(source, schema):
    assert validate_source(source.drop(columns="Price"), schema)["blocking"]
    assert validate_source(source.iloc[:0], schema)["blocking"]


def test_malformed_date_and_missing_key(source, schema):
    source["InvoiceDate"] = source["InvoiceDate"].astype(object)
    source.loc[0, "InvoiceDate"] = "not-a-date"
    source.loc[1, "Invoice"] = None
    report = validate_source(source, schema)
    assert report["issues"]["invalid_date"] == 1
    assert report["issues"]["Invoice:null"] == 1
    assert report["issues"]["negative_price"] == 1


def test_duplicate_primary_and_broken_foreign_keys():
    with pytest.raises(ValueError, match="Primary key"):
        assert_primary_key(pd.DataFrame({"id": [1, 1]}), "id")
    with pytest.raises(ValueError, match="Primary key"):
        assert_primary_key(pd.DataFrame({"id": [1, None]}), "id")
    with pytest.raises(ValueError, match="orphan"):
        assert_foreign_key(pd.DataFrame({"id": [2]}), pd.DataFrame({"id": [1]}), "id")


def test_invalid_inference_categories_and_nonfinite():
    with pytest.raises(ValueError, match="category"):
        validate_inference(pd.DataFrame({"weekday": [8]}), ["weekday"])
    with pytest.raises(ValueError, match="Invalid numeric"):
        validate_inference(pd.DataFrame({"lag_7": [np.inf]}), ["lag_7"])
    with pytest.raises(ValueError, match="missing"):
        validate_inference(pd.DataFrame({"wrong": [1]}), ["lag_7"])


def test_empty_and_bad_encoding(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_bytes(b"")
    with pytest.raises(pd.errors.EmptyDataError):
        read_frame(path)
    path.write_bytes(b"name\n\xff\n")
    with pytest.raises(UnicodeDecodeError):
        read_frame(path)


@pytest.mark.parametrize(
    "name",
    [
        "../escape.csv",
        "/absolute.csv",
        "C:/escape.csv",
        "folder/../../escape.csv",
        "..\\escape.csv",
    ],
)
def test_archive_traversal_rejected(tmp_path, name):
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr(name, "untrusted")
    with pytest.raises(ValueError, match="Unsafe"):
        safe_extract(archive, tmp_path / "output", 10000)
    assert not (tmp_path / "escape.csv").exists()


def test_archive_size_and_existing_raw_integrity(tmp_path):
    archive = tmp_path / "safe.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("data.csv", "id\n1\n")
    with pytest.raises(ValueError, match="limit"):
        safe_extract(archive, tmp_path / "output", 1)
    output = safe_extract(archive, tmp_path / "output", 1000)[0]
    assert safe_extract(archive, tmp_path / "output", 1000) == [output]
    output.write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="differs"):
        safe_extract(archive, tmp_path / "output", 1000)
