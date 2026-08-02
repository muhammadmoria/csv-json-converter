import io
import csv
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from config.config import (
    SUPPORTED_DELIMITERS,
    SUPPORTED_ENCODINGS,
    PREVIEW_ROW_LIMIT,
)
from utils.helpers import format_file_size


def detect_delimiter(first_bytes: bytes) -> str:
    """Detect CSV delimiter by analyzing frequency of candidate characters."""
    try:
        text = first_bytes.decode("utf-8", errors="replace")
    except Exception:
        text = first_bytes.decode("latin-1")

    lines = text.split("\n")[:5]
    if not lines:
        return ","

    # Count occurrences of each delimiter
    counts: dict[str, int] = {}
    for delim in SUPPORTED_DELIMITERS:
        counts[delim] = 0

    for line in lines:
        for delim in SUPPORTED_DELIMITERS:
            counts[delim] += line.count(delim)

    # Return the delimiter with highest count (minimum threshold)
    best = max(counts, key=counts.get)  # type: ignore
    if counts[best] == 0:
        return ","
    return best


def read_csv_file(
    file_path: Path,
    delimiter: Optional[str] = None,
    encoding: Optional[str] = None,
) -> pd.DataFrame:
    """Read and parse a CSV file into a pandas DataFrame.

    Args:
        file_path: Path to the CSV file.
        delimiter: Explicit delimiter override. None for auto-detection.
        encoding: Explicit encoding override. None for auto-detection.

    Returns:
        Parsed pandas DataFrame.

    Raises:
        ValueError: If the file cannot be parsed.
    """
    if not file_path.exists():
        raise ValueError(f"File not found: {file_path}")

    if file_path.stat().st_size == 0:
        raise ValueError("The uploaded file is empty.")

    # Detect encoding if not provided
    if encoding is None:
        encoding = _detect_file_encoding(file_path)

    # Detect delimiter if not provided
    if delimiter is None:
        with open(file_path, "rb") as f:
            first_bytes = f.read(4096)
        delimiter = detect_delimiter(first_bytes)

    # Read the CSV
    try:
        df = pd.read_csv(
            file_path,
            delimiter=delimiter,
            encoding=encoding,
            dtype=str,  # Read all as strings initially for safety
            keep_default_na=False,
            on_bad_lines="warn",
        )
    except UnicodeDecodeError:
        # Try fallback encodings
        for enc in SUPPORTED_ENCODINGS:
            if enc == encoding:
                continue
            try:
                df = pd.read_csv(
                    file_path,
                    delimiter=delimiter,
                    encoding=enc,
                    dtype=str,
                    keep_default_na=False,
                    on_bad_lines="warn",
                )
                encoding = enc
                break
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
        else:
            raise ValueError(
                "We couldn't decode this file as UTF-8. "
                "Try saving it as UTF-8 CSV."
            )
    except pd.errors.EmptyDataError:
        raise ValueError("The CSV file contains no data.")
    except pd.errors.ParserError as e:
        raise ValueError(f"The CSV file is malformed: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unable to parse the CSV file: {str(e)}")

    if df.empty:
        raise ValueError("The CSV file contains no data rows.")

    # Validate consistent columns
    if df.columns is None or len(df.columns) == 0:
        raise ValueError("The CSV file has no column headers.")

    return df


def _detect_file_encoding(file_path: Path) -> str:
    """Detect file encoding by trying encodings in order."""
    # Check for BOM first
    with open(file_path, "rb") as f:
        raw_start = f.read(3)

    if raw_start.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"

    for enc in SUPPORTED_ENCODINGS:
        try:
            with open(file_path, "r", encoding=enc) as f:
                f.read(8192)
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue

    return "latin-1"  # Fallback that accepts all byte values


def get_preview_info(
    df: pd.DataFrame,
    file_path: Path,
    delimiter: str,
    encoding: str,
) -> dict[str, Any]:
    """Generate preview information for the parsed CSV."""
    total_rows = len(df)
    total_columns = len(df.columns)

    # Preview rows (limited)
    preview_df = df.head(PREVIEW_ROW_LIMIT)
    preview_rows = preview_df.to_dict(orient="records")

    # Replace NaN/NaT values in preview with None for JSON
    for row in preview_rows:
        for key in row:
            if pd.isna(row[key]) or row[key] == "":
                row[key] = None

    # Count null/empty values
    null_count = int((df == "").sum().sum())
    try:
        null_count += int(df.isna().sum().sum())
    except Exception:
        pass

    # Count duplicate rows
    duplicate_count = int(df.duplicated().sum())

    # Column names
    columns = list(df.columns)

    return {
        "columns": columns,
        "preview_rows": preview_rows,
        "total_rows": total_rows,
        "total_columns": total_columns,
        "delimiter": delimiter,
        "delimiter_display": {
            ",": "Comma (,)",
            ";": "Semicolon (;)",
            "\t": "Tab",
            "|": "Pipe (|)",
        }.get(delimiter, delimiter),
        "encoding": encoding,
        "null_values": null_count,
        "duplicate_rows": duplicate_count,
        "file_size": format_file_size(file_path.stat().st_size),
        "filename": file_path.name,
    }
