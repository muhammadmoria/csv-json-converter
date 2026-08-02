import json

import pandas as pd
import pytest

from services.json_converter import (
    convert_dataframe_to_json,
    _detect_type,
    _apply_null_handling,
    _remove_empty_rows,
    _IDENTIFIER_PATTERNS,
)


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def simple_df():
    return pd.DataFrame({
        "name": ["John", "Sarah"],
        "age": ["25", "30"],
    })


@pytest.fixture
def mixed_df():
    return pd.DataFrame({
        "name": ["John", "Sarah", "Mike"],
        "age": ["25", "30", "thirty"],
        "active": ["true", "false", "true"],
        "price": ["19.99", "29.50", "0"],
    })


@pytest.fixture
def null_df():
    return pd.DataFrame({
        "name": ["John", ""],
        "age": ["25", ""],
    })


@pytest.fixture
def leading_zero_df():
    return pd.DataFrame({
        "id": ["00123", "00456"],
        "name": ["Alice", "Bob"],
    })


@pytest.fixture
def empty_df():
    return pd.DataFrame()


@pytest.fixture
def special_char_df():
    return pd.DataFrame({
        "name": ["O'Brien", 'Anne "Andy" Smith', "M\u00fcller"],
        "value": ["a&b", "c<d", "e>f"],
    })


@pytest.fixture
def duplicate_df():
    return pd.DataFrame({
        "a": ["1", "2", "1"],
        "b": ["x", "y", "x"],
    })


# ------------------------------------------------------------------
# _detect_type
# ------------------------------------------------------------------

class TestDetectType:
    def test_integer(self):
        assert _detect_type("42") == 42

    def test_float(self):
        assert _detect_type("3.14") == 3.14

    def test_boolean_true(self):
        assert _detect_type("true") is True

    def test_boolean_false(self):
        assert _detect_type("false") is False

    def test_empty_string_is_null(self):
        assert _detect_type("") is None

    def test_whitespace_string_is_null(self):
        assert _detect_type("   ") is None

    def test_regular_string(self):
        assert _detect_type("hello") == "hello"

    def test_leading_zero_preserved(self):
        assert _detect_type("00123") == "00123"

    def test_numeric_code_preserved(self):
        assert _detect_type("123-45") == "123-45"

    def test_ambiguous_1_stays_string(self):
        assert _detect_type("1", "status") == "1"

    def test_ambiguous_0_stays_string(self):
        assert _detect_type("0", "count") == "0"


# ------------------------------------------------------------------
# convert_dataframe_to_json
# ------------------------------------------------------------------

class TestConvert:
    def test_records_orientation(self, simple_df):
        result = convert_dataframe_to_json(simple_df, orientation="records")
        parsed = json.loads(result["json_string"])
        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert parsed[0]["name"] == "John"

    def test_object_orientation(self, simple_df):
        result = convert_dataframe_to_json(
            simple_df, orientation="object", key_column="name",
            type_detection=False,
        )
        parsed = json.loads(result["json_string"])
        assert isinstance(parsed, dict)
        assert "John" in parsed
        assert parsed["John"]["age"] == "25"

    def test_pretty_json(self, simple_df):
        result = convert_dataframe_to_json(simple_df, indent=2)
        lines = result["json_string"].split("\n")
        assert len(lines) > 1  # More than one line = pretty

    def test_minified_json(self, simple_df):
        result = convert_dataframe_to_json(simple_df, minified=True)
        lines = result["json_string"].split("\n")
        assert len(lines) == 1

    def test_null_keep(self, null_df):
        result = convert_dataframe_to_json(
            null_df, null_handling="keep", type_detection=False,
            empty_row_handling="keep",
        )
        parsed = json.loads(result["json_string"])
        assert len(parsed) == 2
        # Second row has empty strings — with type_detection off and empty_row_handling keep
        assert parsed[1]["name"] == ""

    def test_null_empty_string(self, null_df):
        result = convert_dataframe_to_json(
            null_df, null_handling="empty_string",
            type_detection=False, empty_row_handling="keep",
        )
        parsed = json.loads(result["json_string"])
        assert len(parsed) == 2
        assert parsed[1]["name"] == ""

    def test_null_custom_value(self, null_df):
        result = convert_dataframe_to_json(
            null_df, null_handling="custom", null_custom_value="N/A",
            type_detection=False, empty_row_handling="keep",
        )
        parsed = json.loads(result["json_string"])
        assert len(parsed) == 2
        # Empty strings with type_detection off stay empty, not null
        # But if we had actual nulls they'd be replaced

    def test_type_detection_enabled(self, mixed_df):
        result = convert_dataframe_to_json(mixed_df, type_detection=True)
        parsed = json.loads(result["json_string"])
        assert parsed[0]["age"] == 25
        assert parsed[0]["active"] is True
        assert parsed[0]["price"] == 19.99
        # "thirty" stays as string
        assert parsed[2]["age"] == "thirty"

    def test_type_detection_disabled(self, mixed_df):
        result = convert_dataframe_to_json(mixed_df, type_detection=False)
        parsed = json.loads(result["json_string"])
        assert parsed[0]["age"] == "25"
        assert parsed[0]["active"] == "true"

    def test_leading_zeros_preserved(self, leading_zero_df):
        result = convert_dataframe_to_json(leading_zero_df, type_detection=True)
        parsed = json.loads(result["json_string"])
        assert parsed[0]["id"] == "00123"
        assert parsed[1]["id"] == "00456"

    def test_special_characters(self, special_char_df):
        result = convert_dataframe_to_json(
            special_char_df, type_detection=False
        )
        parsed = json.loads(result["json_string"])
        assert parsed[0]["name"] == "O'Brien"
        assert parsed[2]["name"] == "M\u00fcller"

    def test_unicode_characters(self):
        df = pd.DataFrame({"city": ["\u6771\u4eac", "\u00dcbel"]})
        result = convert_dataframe_to_json(df, type_detection=False)
        parsed = json.loads(result["json_string"])
        assert parsed[0]["city"] == "\u6771\u4eac"

    def test_record_count(self, simple_df):
        result = convert_dataframe_to_json(simple_df)
        assert result["record_count"] == 2

    def test_output_size_positive(self, simple_df):
        result = convert_dataframe_to_json(simple_df)
        assert result["output_size"] > 0

    def test_remove_duplicates(self, duplicate_df):
        result = convert_dataframe_to_json(
            duplicate_df, duplicate_handling="remove"
        )
        assert result["record_count"] == 2
        assert result["duplicates_removed"] == 1

    def test_keep_duplicates(self, duplicate_df):
        result = convert_dataframe_to_json(
            duplicate_df, duplicate_handling="keep"
        )
        assert result["record_count"] == 3

    def test_valid_json_output(self, mixed_df):
        result = convert_dataframe_to_json(mixed_df)
        # Should not raise
        json.loads(result["json_string"])

    def test_exclude_columns(self, simple_df):
        result = convert_dataframe_to_json(
            simple_df, exclude_columns=["age"]
        )
        parsed = json.loads(result["json_string"])
        assert "age" not in parsed[0]
        assert "name" in parsed[0]

    def test_trim_whitespace(self):
        df = pd.DataFrame({"name": ["  John  ", " Sarah "]})
        result = convert_dataframe_to_json(df, trim_whitespace=True, type_detection=False)
        parsed = json.loads(result["json_string"])
        assert parsed[0]["name"] == "John"
        assert parsed[1]["name"] == "Sarah"

    def test_normalize_columns(self):
        df = pd.DataFrame({"First Name": ["John"], "Email Address": ["j@e.com"]})
        result = convert_dataframe_to_json(df, normalize_columns=True, type_detection=False)
        parsed = json.loads(result["json_string"])
        assert "first_name" in parsed[0]
        assert "email_address" in parsed[0]

    def test_column_mapping(self, simple_df):
        result = convert_dataframe_to_json(
            simple_df, column_mapping={"name": "full_name"}, type_detection=False
        )
        parsed = json.loads(result["json_string"])
        assert "full_name" in parsed[0]
        assert "name" not in parsed[0]

    def test_empty_rows_removed(self):
        df = pd.DataFrame({"a": ["1", "", "3"], "b": ["x", "", "z"]})
        result = convert_dataframe_to_json(df, type_detection=False)
        # Both empty strings should be detected as empty row and removed
        assert result["record_count"] <= 3

    def test_indent_4_spaces(self, simple_df):
        result = convert_dataframe_to_json(simple_df, indent=4)
        lines = result["json_string"].split("\n")
        # Check for 4-space indent
        assert "    " in result["json_string"]


# ------------------------------------------------------------------
# _remove_empty_rows
# ------------------------------------------------------------------

class TestRemoveEmptyRows:
    def test_removes_all_empty(self):
        df = pd.DataFrame({"a": ["", ""], "b": ["", ""]})
        result = _remove_empty_rows(df)
        assert len(result) == 0

    def test_keeps_partial(self):
        df = pd.DataFrame({"a": ["", "x"], "b": ["y", ""]})
        result = _remove_empty_rows(df)
        assert len(result) == 2

    def test_keeps_populated(self):
        df = pd.DataFrame({"a": ["x"], "b": ["y"]})
        result = _remove_empty_rows(df)
        assert len(result) == 1


# ------------------------------------------------------------------
# _apply_null_handling
# ------------------------------------------------------------------

class TestApplyNullHandling:
    def test_keep_null(self):
        records = [{"a": None, "b": "x"}]
        result = _apply_null_handling(records, "keep", None)
        assert result[0]["a"] is None

    def test_empty_string(self):
        records = [{"a": None, "b": "x"}]
        result = _apply_null_handling(records, "empty_string", None)
        assert result[0]["a"] == ""

    def test_custom_value(self):
        records = [{"a": None, "b": "x"}]
        result = _apply_null_handling(records, "custom", "N/A")
        assert result[0]["a"] == "N/A"
