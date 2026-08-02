"""Flask route definitions for the CSV to JSON converter."""

import json
import os
import time
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
    send_file,
)

from services.csv_parser import read_csv_file, get_preview_info
from services.json_converter import convert_dataframe_to_json
from services.validators import (
    validate_file,
    validate_conversion_options,
    validate_file_path,
)
from utils.helpers import (
    Timer,
    build_api_response,
    format_file_size,
    make_safe_filename,
)
import config.config as cfg

converter_bp = Blueprint("converter", __name__)


@converter_bp.route("/")
def index():
    """Render the main page."""
    return render_template("index.html")


@converter_bp.route("/api/health")
def health():
    """Health check endpoint."""
    return jsonify(build_api_response(True, {"status": "ok"}))


@converter_bp.route("/api/preview", methods=["POST"])
def preview():
    """Upload and preview a CSV file."""
    # Validate file
    if "file" not in request.files:
        return jsonify(build_api_response(
            False, error_code="NO_FILE",
            error_message="Please upload a CSV file.",
        )), 400

    file_storage = request.files["file"]
    error, file_path = validate_file(file_storage)
    if error:
        return jsonify(build_api_response(
            False, error_code="INVALID_FILE",
            error_message=error,
        )), 400

    try:
        df = read_csv_file(file_path)

        # Get delimiter and encoding from config defaults
        delimiter = request.form.get("delimiter")
        encoding = request.form.get("encoding")

        info = get_preview_info(df, file_path, delimiter or ",", encoding or "utf-8")
        info["file_id"] = file_path.name

        return jsonify(build_api_response(True, info))

    except ValueError as e:
        # Clean up the uploaded file on parse failure
        _safe_delete(file_path)
        return jsonify(build_api_response(
            False, error_code="PARSE_ERROR",
            error_message=str(e),
        )), 422
    except Exception:
        _safe_delete(file_path)
        return jsonify(build_api_response(
            False, error_code="UNKNOWN_ERROR",
            error_message="Unable to process the CSV file.",
        )), 500


@converter_bp.route("/api/convert", methods=["POST"])
def convert():
    """Convert a previously uploaded CSV to JSON."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify(build_api_response(
            False, error_code="INVALID_REQUEST",
            error_message="Invalid request body.",
        )), 400

    file_id = data.get("file_id")
    if not file_id:
        return jsonify(build_api_response(
            False, error_code="NO_FILE",
            error_message="No file specified for conversion.",
        )), 400

    # Validate and locate the file
    file_path = cfg.UPLOAD_FOLDER / make_safe_filename(file_id)
    if not file_path.suffix.lower() == ".csv":
        file_path = file_path.with_suffix(".csv")

    path_error, _ = validate_file_path(file_path)
    if path_error:
        return jsonify(build_api_response(
            False, error_code="INVALID_FILE",
            error_message=path_error,
        )), 400

    # Build options
    options = {
        "orientation": data.get("orientation", "records"),
        "indent": data.get("indent", 2),
        "null_handling": data.get("null_handling", "keep"),
        "null_custom_value": data.get("null_custom_value"),
        "type_detection": data.get("type_detection", True),
        "key_column": data.get("key_column"),
        "minified": data.get("minified", False),
        "duplicate_handling": data.get("duplicate_handling", "keep"),
        "empty_row_handling": data.get("empty_row_handling", "remove_empty"),
        "include_columns": data.get("include_columns"),
        "exclude_columns": data.get("exclude_columns"),
        "column_mapping": data.get("column_mapping"),
        "trim_whitespace": data.get("trim_whitespace", False),
        "normalize_columns": data.get("normalize_columns", False),
    }

    # Validate options
    opt_error, _ = validate_conversion_options(options)
    if opt_error:
        return jsonify(build_api_response(
            False, error_code="INVALID_OPTIONS",
            error_message=opt_error,
        )), 400

    try:
        # Parse CSV
        df = read_csv_file(file_path)

        # Detect delimiter and encoding from preview data
        delimiter = data.get("delimiter")
        encoding = data.get("encoding")

        # Convert
        with Timer() as t:
            result = convert_dataframe_to_json(df, **options)

        json_string = result["json_string"]
        record_count = result["record_count"]
        output_size = result["output_size"]
        processing_time = round(t.elapsed_ms)

        # Save output file for download
        output_filename = file_path.stem + ".json"
        output_path = cfg.OUTPUT_FOLDER / make_safe_filename(output_filename)
        output_path.write_text(json_string, encoding="utf-8")

        response_data = {
            "json_string": json_string,
            "record_count": record_count,
            "output_size": format_file_size(output_size),
            "processing_time_ms": processing_time,
            "output_filename": output_path.name,
            "file_id": file_path.name,
        }

        return jsonify(build_api_response(True, response_data))

    except ValueError as e:
        return jsonify(build_api_response(
            False, error_code="CONVERSION_ERROR",
            error_message=str(e),
        )), 422
    except Exception:
        return jsonify(build_api_response(
            False, error_code="UNKNOWN_ERROR",
            error_message="Unable to convert the CSV.",
        )), 500


@converter_bp.route("/api/download/<filename>")
def download(filename):
    """Download a generated JSON file."""
    safe_name = make_safe_filename(filename)
    if not safe_name.endswith(".json"):
        safe_name += ".json"

    file_path = cfg.OUTPUT_FOLDER / safe_name

    # Validate path
    try:
        resolved = file_path.resolve()
        output_resolved = cfg.OUTPUT_FOLDER.resolve()
        if not str(resolved).startswith(str(output_resolved)):
            return jsonify(build_api_response(
                False, error_code="INVALID_PATH",
                error_message="Invalid file path.",
            )), 400
    except (ValueError, OSError):
        return jsonify(build_api_response(
            False, error_code="INVALID_PATH",
            error_message="Invalid file path.",
        )), 400

    if not file_path.exists():
        return jsonify(build_api_response(
            False, error_code="FILE_NOT_FOUND",
            error_message="File not found. Please convert again.",
        )), 404

    return send_file(
        str(file_path),
        mimetype="application/json",
        as_attachment=True,
        download_name=safe_name,
    )


def _safe_delete(file_path: Path):
    """Safely delete a temporary file."""
    try:
        if file_path.exists():
            file_path.unlink()
    except OSError:
        pass
