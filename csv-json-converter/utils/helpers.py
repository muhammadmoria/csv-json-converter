"""Utility helper functions."""

import json
import re
import time
from typing import Any


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable form."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def normalize_column_name(name: str) -> str:
    """Normalize a column name to snake_case."""
    if not name:
        return name
    # Replace non-alphanumeric with spaces
    cleaned = re.sub(r"[^a-zA-Z0-9]", " ", name)
    # Split on spaces and lowercase
    parts = cleaned.lower().split()
    if not parts:
        return name.lower()
    return "_".join(parts)


def sanitize_json_value(value: Any) -> Any:
    """Sanitize a value for safe JSON serialization.

    Converts NumPy types, handles NaN/Inf, and ensures
    the value is JSON-serializable.
    """
    if value is None:
        return None

    # Handle pandas/NumPy types
    try:
        import numpy as np
        if isinstance(value, (np.integer,)):
            return int(value)
        if isinstance(value, (np.floating,)):
            if np.isnan(value) or np.isinf(value):
                return None
            return float(value)
        if isinstance(value, np.bool_):
            return bool(value)
        if isinstance(value, (np.ndarray,)):
            return value.tolist()
    except ImportError:
        pass

    # Handle pandas Timestamp/NaT
    try:
        import pandas as pd
        if isinstance(value, pd.Timestamp):
            return value.isoformat()
        if pd.isna(value):
            return None
    except ImportError:
        pass

    # Handle Python float NaN/Inf
    if isinstance(value, float):
        import math
        if math.isnan(value) or math.isinf(value):
            return None

    return value


def make_safe_filename(filename: str) -> str:
    """Create a safe filename from user input."""
    import os
    # Remove path components
    filename = os.path.basename(filename)
    # Remove null bytes
    filename = filename.replace("\x00", "")
    # Keep only safe characters
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    return filename


class Timer:
    """Context manager for timing operations."""

    def __init__(self):
        self.elapsed_ms: float = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000


def build_api_response(success: bool, data: Any = None,
                       error_code: str = None, error_message: str = None) -> dict:
    """Build a standardized API response."""
    response: dict = {"success": success}
    if success:
        response["data"] = data
    else:
        response["error"] = {
            "code": error_code or "UNKNOWN_ERROR",
            "message": error_message or "An unexpected error occurred.",
        }
    return response


def detect_encoding(file_path: str) -> str:
    """Attempt to detect file encoding."""
    import chardet  # type: ignore
    try:
        with open(file_path, "rb") as f:
            raw = f.read(4096)
        result = chardet.detect(raw)
        encoding = result.get("encoding", "utf-8")
        if encoding and encoding.lower().replace("-", "") in ("utf8", "utf8sig"):
            return "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"
        return encoding or "utf-8"
    except Exception:
        return "utf-8"
