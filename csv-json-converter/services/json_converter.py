"""JSON conversion service.

Responsible for converting pandas DataFrames to JSON with
various formatting and transformation options.
"""

import json
import re
from typing import Any, Optional

import pandas as pd

from utils.helpers import sanitize_json_value, normalize_column_name


# Patterns that suggest a value is an identifier (should be kept as string)
# Note: only use hyphen (not dot) as separator, to avoid matching floats like 3.14
_IDENTIFIER_PATTERNS = [
    re.compile(r"^0[0-9]+"),           # Leading zeros: 00123
    re.compile(r"^[0-9]+-[0-9]"),     # Numeric with hyphen separator: 123-45
    re.compile(r"^[A-Za-z]?[0-9]+-[A-Za-z0-9]"),  # Alphanumeric codes
]


def convert_dataframe_to_json(
    df: pd.DataFrame,
    orientation: str = "records",
    indent: int = 2,
    null_handling: str = "keep",
    null_custom_value: Optional[str] = None,
    type_detection: bool = True,
    key_column: Optional[str] = None,
    minified: bool = False,
    duplicate_handling: str = "keep",
    empty_row_handling: str = "remove_empty",
    include_columns: Optional[list[str]] = None,
    exclude_columns: Optional[list[str]] = None,
    column_mapping: Optional[dict[str, str]] = None,
    trim_whitespace: bool = False,
    normalize_columns: bool = False,
) -> dict[str, Any]:
    """Convert a DataFrame to JSON with the given options.

    Args:
        df: Input DataFrame.
        orientation: 'records' or 'object'.
        indent: Number of spaces for indentation (ignored if minified).
        null_handling: 'keep', 'empty_string', or 'custom'.
        null_custom_value: Value to use when null_handling is 'custom'.
        type_detection: Whether to auto-detect types.
        key_column: Column to use as key in 'object' orientation.
        minified: Whether to output minified JSON.
        duplicate_handling: 'keep' or 'remove'.
        empty_row_handling: 'keep' or 'remove_empty'.
        include_columns: Columns to include (None = all).
        exclude_columns: Columns to exclude.
        column_mapping: Rename columns {old: new}.
        trim_whitespace: Trim whitespace from values.
        normalize_columns: Normalize column names to snake_case.

    Returns:
        Dict with 'json_string', 'record_count', 'output_size'.
    """
    # Work on a copy
    df = df.copy()

    # Apply column transformations
    df, column_map = _apply_column_transformations(
        df, include_columns, exclude_columns, column_mapping,
        trim_whitespace, normalize_columns,
    )

    # Handle empty rows
    if empty_row_handling == "remove_empty":
        df = _remove_empty_rows(df)

    # Handle duplicates
    if duplicate_handling == "remove":
        original_count = len(df)
        df = df.drop_duplicates()
        removed = original_count - len(df)
    else:
        removed = 0

    # Convert values
    records = _dataframe_to_records(df, type_detection)

    # Handle nulls
    records = _apply_null_handling(records, null_handling, null_custom_value)

    # Build output structure
    if orientation == "object" and key_column:
        result = _build_object_output(records, key_column, column_map)
    else:
        result = records

    # Serialize
    actual_indent = None if minified else indent
    json_string = json.dumps(result, indent=actual_indent, ensure_ascii=False)

    # Calculate output size
    output_size = len(json_string.encode("utf-8"))
    record_count = len(records)

    return {
        "json_string": json_string,
        "record_count": record_count,
        "output_size": output_size,
        "duplicates_removed": removed,
    }


def _apply_column_transformations(
    df: pd.DataFrame,
    include_columns: Optional[list[str]],
    exclude_columns: Optional[list[str]],
    column_mapping: Optional[dict[str, str]],
    trim_whitespace: bool,
    normalize_columns: bool,
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Apply column filtering, renaming, and normalization."""
    # Build effective column mapping (applied after other transforms)
    effective_mapping: dict[str, str] = {}

    # Include/exclude columns
    if include_columns:
        # Map back if columns were previously renamed
        valid = [c for c in include_columns if c in df.columns]
        df = df[valid]

    if exclude_columns:
        to_exclude = [c for c in exclude_columns if c in df.columns]
        df = df.drop(columns=to_exclude)

    # Normalize column names
    if normalize_columns:
        rename_map = {}
        for col in df.columns:
            new_name = normalize_column_name(str(col))
            if new_name != col:
                rename_map[col] = new_name
                effective_mapping[col] = new_name
        if rename_map:
            df = df.rename(columns=rename_map)

    # Apply user-provided column mapping
    if column_mapping:
        valid_map = {k: v for k, v in column_mapping.items() if k in df.columns}
        effective_mapping.update(valid_map)
        if valid_map:
            df = df.rename(columns=valid_map)

    # Trim whitespace from values
    if trim_whitespace:
        df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)

    return df, effective_mapping


def _remove_empty_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows where all values are empty/null."""
    # A row is "empty" if all string columns are empty strings
    # and all other columns are NaN
    mask = df.apply(
        lambda row: all(
            str(v).strip() == "" or pd.isna(v)
            for v in row
        ),
        axis=1,
    )
    return df[~mask].reset_index(drop=True)


def _dataframe_to_records(
    df: pd.DataFrame, type_detection: bool
) -> list[dict[str, Any]]:
    """Convert DataFrame to list of record dicts with optional type detection."""
    records = []

    for _, row in df.iterrows():
        record: dict[str, Any] = {}
        for col in df.columns:
            value = row[col]
            value = sanitize_json_value(value)

            if type_detection and value is not None:
                value = _detect_type(value, col)

            record[str(col)] = value
        records.append(record)

    return records


def _detect_type(value: Any, column_name: str = "") -> Any:
    """Attempt to detect the type of a string value.

    Preserves identifiers (leading zeros, codes) as strings.
    """
    if not isinstance(value, str):
        return value

    stripped = value.strip()
    if stripped == "":
        return None

    # Check if this looks like an identifier
    for pattern in _IDENTIFIER_PATTERNS:
        if pattern.match(stripped):
            return stripped

    # Boolean detection
    if stripped.lower() in ("true", "yes", "1") and len(stripped) <= 5:
        # Only detect "1" as boolean if it's standalone
        if stripped == "1" and column_name:
            return stripped  # Ambiguous, keep as string
        return True
    if stripped.lower() in ("false", "no", "0") and len(stripped) <= 5:
        if stripped == "0" and column_name:
            return stripped
        return False

    # Integer detection
    try:
        int_val = int(stripped)
        # Don't convert values that are too long (might be identifiers)
        if len(stripped) > 15:
            return stripped
        return int_val
    except ValueError:
        pass

    # Float detection
    try:
        float_val = float(stripped)
        return float_val
    except ValueError:
        pass

    return stripped


def _apply_null_handling(
    records: list[dict[str, Any]],
    null_handling: str,
    null_custom_value: Optional[str],
) -> list[dict[str, Any]]:
    """Apply null handling strategy to all records."""
    if null_handling == "keep":
        return records

    replacement: Any = None
    if null_handling == "empty_string":
        replacement = ""
    elif null_handling == "custom" and null_custom_value is not None:
        replacement = null_custom_value
    else:
        return records

    for record in records:
        for key in record:
            if record[key] is None:
                record[key] = replacement

    return records


def _build_object_output(
    records: list[dict[str, Any]],
    key_column: str,
    column_map: dict[str, str],
) -> dict[str, Any]:
    """Build an object-oriented JSON structure keyed by a column.

    The key column may have been renamed via column_map,
    so we need to check both the original and mapped names.
    """
    # Determine the actual column name in the records
    actual_key = key_column
    if key_column in column_map:
        actual_key = column_map[key_column]

    # Also check if the key_column is already in the records
    if actual_key not in (records[0].keys() if records else []):
        actual_key = key_column

    result: dict[str, Any] = {}
    for record in records:
        key_value = record.pop(actual_key, None)
        if key_value is None:
            key_value = "null"
        key_str = str(key_value)
        # Handle duplicate keys by appending suffix
        if key_str in result:
            i = 1
            while f"{key_str}_{i}" in result:
                i += 1
            key_str = f"{key_str}_{i}"
        result[key_str] = record

    return result
