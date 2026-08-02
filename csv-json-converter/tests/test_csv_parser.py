import csv
import io
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from services.csv_parser import (
    read_csv_file,
    detect_delimiter,
    get_preview_info,
    _detect_file_encoding,
)


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file."""
    p = tmp_path / "sample.csv"
    p.write_text(
        "name,age,email\n"
        "John,25,john@example.com\n"
        "Sarah,30,sarah@example.com\n"
        "Mike,35,mike@example.com\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def empty_csv(tmp_path):
    p = tmp_path / "empty.csv"
    p.write_text("", encoding="utf-8")
    return p


@pytest.fixture
def headers_only_csv(tmp_path):
    p = tmp_path / "headers.csv"
    p.write_text("a,b,c\n", encoding="utf-8")
    return p


@pytest.fixture
def malformed_csv(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text(
        'name,age\n"unclosed quote, 25\nAlice,30\n',
        encoding="utf-8",
    )
    return p


@pytest.fixture
def semicolon_csv(tmp_path):
    p = tmp_path / "semi.csv"
    p.write_text(
        "name;age;city\n"
        "John;25;NYC\n"
        "Sarah;30;LA\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def tab_csv(tmp_path):
    p = tmp_path / "tab.csv"
    p.write_text(
        "name\tage\ncity\n"
        "John\t25\tNYC\n"
        "Sarah\t30\tLA\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def pipe_csv(tmp_path):
    p = tmp_path / "pipe.csv"
    p.write_text(
        "name|age|city\n"
        "John|25|NYC\n"
        "Sarah|30|LA\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def utf8bom_csv(tmp_path):
    p = tmp_path / "bom.csv"
    p.write_bytes(
        b"\xef\xbb\xbf"
        b"name,age\n"
        b"John,25\n"
    )
    return p


@pytest.fixture
def latin1_csv(tmp_path):
    p = tmp_path / "latin.csv"
    p.write_text(
        "name,city\n"
        "R\xe9n\xe9,Paris\n",
        encoding="latin-1",
    )
    return p


@pytest.fixture
def unicode_csv(tmp_path):
    p = tmp_path / "unicode.csv"
    p.write_text(
        "name,city\n"
        "\u6771\u4eac,Tokyo\n"
        "\u00dcbel,Zurich\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def duplicates_csv(tmp_path):
    p = tmp_path / "dups.csv"
    p.write_text(
        "name,age\n"
        "John,25\n"
        "Sarah,30\n"
        "John,25\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def leading_zeros_csv(tmp_path):
    p = tmp_path / "ids.csv"
    p.write_text(
        "id,name\n"
        "00123,Alice\n"
        "00456,Bob\n",
        encoding="utf-8",
    )
    return p


# ------------------------------------------------------------------
# detect_delimiter
# ------------------------------------------------------------------

class TestDetectDelimiter:
    def test_comma(self):
        result = detect_delimiter(b"name,age\nJohn,25\n")
        assert result == ","

    def test_semicolon(self):
        result = detect_delimiter(b"name;age\nJohn;25\n")
        assert result == ";"

    def test_tab(self):
        result = detect_delimiter(b"name\tage\nJohn\t25\n")
        assert result == "\t"

    def test_pipe(self):
        result = detect_delimiter(b"name|age\nJohn|25\n")
        assert result == "|"

    def test_empty_defaults_to_comma(self):
        result = detect_delimiter(b"")
        assert result == ","


# ------------------------------------------------------------------
# read_csv_file
# ------------------------------------------------------------------

class TestReadCsvFile:
    def test_valid_csv(self, sample_csv):
        df = read_csv_file(sample_csv)
        assert len(df) == 3
        assert list(df.columns) == ["name", "age", "email"]

    def test_empty_csv_raises(self, empty_csv):
        with pytest.raises(ValueError, match="empty"):
            read_csv_file(empty_csv)

    def test_headers_only_raises(self, headers_only_csv):
        with pytest.raises(ValueError, match="no data"):
            read_csv_file(headers_only_csv)

    def test_nonexistent_file_raises(self, tmp_path):
        with pytest.raises(ValueError, match="not found"):
            read_csv_file(tmp_path / "nonexistent.csv")

    def test_semicolon_delimiter(self, semicolon_csv):
        df = read_csv_file(semicolon_csv)
        assert len(df) == 2
        assert list(df.columns) == ["name", "age", "city"]

    def test_tab_delimiter(self, tab_csv):
        df = read_csv_file(tab_csv)
        assert len(df) >= 1

    def test_pipe_delimiter(self, pipe_csv):
        df = read_csv_file(pipe_csv)
        assert len(df) == 2

    def test_utf8_bom(self, utf8bom_csv):
        df = read_csv_file(utf8bom_csv)
        assert len(df) >= 1
        assert "name" in df.columns

    def test_latin1_encoding(self, latin1_csv):
        df = read_csv_file(latin1_csv)
        assert len(df) == 1

    def test_unicode_characters(self, unicode_csv):
        df = read_csv_file(unicode_csv)
        assert len(df) == 2

    def test_malformed_csv_raises(self, malformed_csv):
        # Severely malformed CSV (unclosed quote causing parse error)
        with pytest.raises(ValueError):
            read_csv_file(malformed_csv)


# ------------------------------------------------------------------
# get_preview_info
# ------------------------------------------------------------------

class TestPreviewInfo:
    def test_basic_preview(self, sample_csv):
        df = read_csv_file(sample_csv)
        info = get_preview_info(df, sample_csv, ",", "utf-8")
        assert info["total_rows"] == 3
        assert info["total_columns"] == 3
        assert len(info["columns"]) == 3
        assert len(info["preview_rows"]) == 3
        assert info["delimiter"] == ","

    def test_duplicate_count(self, duplicates_csv):
        df = read_csv_file(duplicates_csv)
        info = get_preview_info(df, duplicates_csv, ",", "utf-8")
        assert info["duplicate_rows"] == 1

    def test_null_count(self, tmp_path):
        p = tmp_path / "nulls.csv"
        p.write_text("a,b\n,\n2,3\n", encoding="utf-8")
        df = read_csv_file(p)
        info = get_preview_info(df, p, ",", "utf-8")
        assert info["null_values"] >= 1
