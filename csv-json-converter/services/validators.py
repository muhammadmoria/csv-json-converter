import os
from pathlib import Path
from typing import Optional, Tuple

import config.config as cfg

ALLOWED_EXTENSIONS = {"csv"}
ALLOWED_MIME_TYPES = {"text/csv", "text/plain", "application/vnd.ms-excel"}


def validate_file(file_storage) -> Tuple[Optional[str], Optional[Path]]:
    """Validate an uploaded file.

    Args:
        file_storage: Flask FileStorage object.

    Returns:
        Tuple of (error_message, None) on failure,
        or (None, safe_file_path) on success.
    """
    if file_storage is None:
        return "No file was provided.", None

    filename = file_storage.filename
    if not filename or filename.strip() == "":
        return "No file was provided.", None

    # Validate extension
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        return (
            f"Unsupported file type '.{ext}'. Please upload a CSV file.",
            None,
        )

    # Validate MIME type if available
    mime = file_storage.mimetype
    if mime and mime != "" and mime not in ALLOWED_MIME_TYPES:
        # Some browsers send different MIME types for CSV
        # Be permissive but log a warning conceptually
        pass

    # Check file size (read content to check)
    content = file_storage.read()
    if len(content) == 0:
        return "The uploaded file is empty.", None

    if len(content) > cfg.MAX_FILE_SIZE_BYTES:
        from utils.helpers import format_file_size
        max_str = format_file_size(cfg.MAX_FILE_SIZE_BYTES)
        return (
            f"The file exceeds the maximum allowed size of {max_str}.",
            None,
        )

    # Reset file pointer
    file_storage.seek(0)

    # Save with safe filename
    from utils.helpers import make_safe_filename
    safe_name = make_safe_filename(filename)
    if not safe_name.endswith(".csv"):
        safe_name += ".csv"

    upload_path = cfg.UPLOAD_FOLDER / safe_name

    # Handle name collisions
    counter = 1
    base = upload_path.stem
    while upload_path.exists():
        upload_path = cfg.UPLOAD_FOLDER / f"{base}_{counter}.csv"
        counter += 1

    file_storage.save(str(upload_path))
    return None, upload_path


def validate_conversion_options(options: dict) -> Tuple[Optional[str], None]:
    """Validate conversion options.

    Returns:
        Tuple of (error_message, None) on failure, (None, None) on success.
    """
    orientation = options.get("orientation", "records")
    if orientation not in ("records", "object"):
        return "Invalid orientation. Use 'records' or 'object'.", None

    if orientation == "object":
        key_column = options.get("key_column")
        if not key_column:
            return (
                "A key column must be specified for object orientation.",
                None,
            )

    indent = options.get("indent", 2)
    if not isinstance(indent, int) or indent < 0 or indent > 8:
        return "Indent must be an integer between 0 and 8.", None

    null_handling = options.get("null_handling", "keep")
    if null_handling not in ("keep", "empty_string", "custom"):
        return "Invalid null handling option.", None

    if null_handling == "custom":
        if "null_custom_value" not in options or options["null_custom_value"] is None:
            return "A custom null value must be provided.", None

    type_detection = options.get("type_detection", True)
    if not isinstance(type_detection, bool):
        return "Type detection must be a boolean.", None

    minified = options.get("minified", False)
    if not isinstance(minified, bool):
        return "Minified must be a boolean.", None

    duplicate_handling = options.get("duplicate_handling", "keep")
    if duplicate_handling not in ("keep", "remove"):
        return "Invalid duplicate handling option.", None

    empty_row_handling = options.get("empty_row_handling", "remove_empty")
    if empty_row_handling not in ("keep", "remove_empty"):
        return "Invalid empty row handling option.", None

    return None, None


def validate_file_path(file_path: Path) -> Tuple[Optional[str], None]:
    """Validate that a file path is safe and within the uploads directory.

    Returns:
        Tuple of (error_message, None) on failure, (None, None) on success.
    """
    try:
        resolved = file_path.resolve()
        upload_resolved = cfg.UPLOAD_FOLDER.resolve()

        # Ensure the file is within the uploads directory
        if not str(resolved).startswith(str(upload_resolved)):
            return "Invalid file path.", None

        if not resolved.exists():
            return "File not found.", None

        if resolved.suffix.lower() != ".csv":
            return "Invalid file type.", None

        return None, None
    except (ValueError, OSError):
        return "Invalid file path.", None
