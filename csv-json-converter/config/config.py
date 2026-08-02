"""Application configuration module."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Flask configuration
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
FLASK_ENV = os.getenv("FLASK_ENV", "production")
DEBUG = FLASK_ENV == "development"

# File upload configuration
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "16"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {"csv"}
ALLOWED_MIME_TYPES = {"text/csv", "text/plain", "application/vnd.ms-excel"}
UPLOAD_FOLDER = BASE_DIR / "uploads"
OUTPUT_FOLDER = BASE_DIR / "output"

# CSV parsing configuration
SUPPORTED_DELIMITERS = [",", ";", "\t", "|"]
SUPPORTED_ENCODINGS = ["utf-8", "utf-8-sig", "latin-1"]
PREVIEW_ROW_LIMIT = 20

# JSON conversion defaults
DEFAULT_INDENT = 2
DEFAULT_ORIENTATION = "records"
DEFAULT_NULL_HANDLING = "keep"
DEFAULT_TYPE_DETECTION = True
DEFAULT_DUPLICATE_HANDLING = "keep"
DEFAULT_EMPTY_ROW_HANDLING = "remove_empty"
DEFAULT_TRIM_WHITESPACE = False
DEFAULT_NORMALIZE_COLUMNS = False
