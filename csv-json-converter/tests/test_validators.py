import io
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from services.validators import (
    validate_file,
    validate_conversion_options,
    validate_file_path,
)
import config.config as cfg


# ------------------------------------------------------------------
# validate_file
# ------------------------------------------------------------------

class TestValidateFile:
    def _make_file_storage(self, filename, content=b"a,b\n1,2\n", mime="text/csv"):
        fs = MagicMock()
        fs.filename = filename
        fs.mimetype = mime
        fs.read.return_value = content
        # Make save actually write the file
        def fake_save(dest):
            p = Path(dest)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(content)
        fs.save.side_effect = fake_save
        return fs

    def test_valid_csv(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cfg, "UPLOAD_FOLDER", tmp_path)
        fs = self._make_file_storage("test.csv")
        error, path = validate_file(fs)
        assert error is None
        assert path is not None
        assert path.exists()

    def test_no_file(self):
        error, path = validate_file(None)
        assert "No file" in error
        assert path is None

    def test_empty_filename(self):
        fs = MagicMock()
        fs.filename = ""
        fs.mimetype = ""
        error, path = validate_file(fs)
        assert error is not None

    def test_invalid_extension(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cfg, "UPLOAD_FOLDER", tmp_path)
        fs = self._make_file_storage("test.txt")
        error, path = validate_file(fs)
        assert "Unsupported" in error
        assert path is None

    def test_empty_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cfg, "UPLOAD_FOLDER", tmp_path)
        fs = self._make_file_storage("empty.csv", content=b"")
        error, path = validate_file(fs)
        assert "empty" in error.lower()

    def test_oversized_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cfg, "UPLOAD_FOLDER", tmp_path)
        monkeypatch.setattr(cfg, "MAX_FILE_SIZE_BYTES", 100)
        fs = self._make_file_storage("big.csv", content=b"x" * 200)
        error, path = validate_file(fs)
        assert "exceeds" in error.lower()

    def test_safe_filename(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cfg, "UPLOAD_FOLDER", tmp_path)
        fs = self._make_file_storage("../../../etc/passwd.csv")
        error, path = validate_file(fs)
        assert error is None
        assert path.name != "../../../etc/passwd.csv"
        assert "etc_passwd.csv" in path.name or "passwd.csv" in path.name


# ------------------------------------------------------------------
# validate_conversion_options
# ------------------------------------------------------------------

class TestValidateOptions:
    def test_valid_options(self):
        opts = {"orientation": "records", "indent": 2}
        error, _ = validate_conversion_options(opts)
        assert error is None

    def test_invalid_orientation(self):
        opts = {"orientation": "invalid"}
        error, _ = validate_conversion_options(opts)
        assert "orientation" in error.lower()

    def test_object_without_key(self):
        opts = {"orientation": "object", "key_column": None}
        error, _ = validate_conversion_options(opts)
        assert "key column" in error.lower()

    def test_object_with_key(self):
        opts = {"orientation": "object", "key_column": "id"}
        error, _ = validate_conversion_options(opts)
        assert error is None

    def test_invalid_indent(self):
        opts = {"indent": -1}
        error, _ = validate_conversion_options(opts)
        assert "indent" in error.lower()

    def test_invalid_null_handling(self):
        opts = {"null_handling": "maybe"}
        error, _ = validate_conversion_options(opts)
        assert error is not None

    def test_custom_null_without_value(self):
        opts = {"null_handling": "custom"}
        error, _ = validate_conversion_options(opts)
        assert "custom null" in error.lower()

    def test_custom_null_with_value(self):
        opts = {"null_handling": "custom", "null_custom_value": "N/A"}
        error, _ = validate_conversion_options(opts)
        assert error is None

    def test_invalid_type_detection(self):
        opts = {"type_detection": "yes"}
        error, _ = validate_conversion_options(opts)
        assert "boolean" in error.lower()


# ------------------------------------------------------------------
# validate_file_path
# ------------------------------------------------------------------

class TestValidateFilePath:
    def test_valid_path(self, tmp_path, monkeypatch):
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()
        monkeypatch.setattr(cfg, "UPLOAD_FOLDER", upload_dir)

        csv_file = upload_dir / "test.csv"
        csv_file.write_text("a,b\n1,2")

        error, _ = validate_file_path(csv_file)
        assert error is None

    def test_path_traversal(self, tmp_path, monkeypatch):
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()
        monkeypatch.setattr(cfg, "UPLOAD_FOLDER", upload_dir)

        evil = tmp_path / "etc" / "passwd"
        error, _ = validate_file_path(evil)
        assert error is not None

    def test_nonexistent(self, tmp_path, monkeypatch):
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()
        monkeypatch.setattr(cfg, "UPLOAD_FOLDER", upload_dir)

        error, _ = validate_file_path(upload_dir / "nope.csv")
        assert "not found" in error.lower()
