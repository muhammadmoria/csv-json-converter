"""Tests for Flask routes."""

import io
import json
import os
from pathlib import Path

import pytest

from app import create_app
import config.config as cfg


def _upload_first(client, csv_bytes):
    """Upload a CSV and return the file_id."""
    data = {"file": (io.BytesIO(csv_bytes), "convert_test.csv")}
    resp = client.post("/api/preview", data=data, content_type="multipart/form-data")
    result = resp.get_json()
    assert result["success"] is True
    return result["data"]["file_id"]


@pytest.fixture
def app(tmp_path):
    """Create app with temporary upload/output folders."""
    upload = tmp_path / "uploads"
    output = tmp_path / "output"
    upload.mkdir()
    output.mkdir()

    application = create_app()
    application.config["TESTING"] = True

    # Monkey-patch the config module's paths (used via module reference)
    cfg.UPLOAD_FOLDER = upload
    cfg.OUTPUT_FOLDER = output

    return application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_csv_bytes():
    return b"name,age,email\nJohn,25,john@example.com\nSarah,30,sarah@example.com\n"


class TestGetIndex:
    def test_index_returns_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"CSV" in resp.data


class TestHealthEndpoint:
    def test_health_ok(self, client):
        resp = client.get("/api/health")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["success"] is True
        assert data["data"]["status"] == "ok"


class TestPreviewEndpoint:
    def test_valid_upload(self, client, sample_csv_bytes):
        data = {"file": (io.BytesIO(sample_csv_bytes), "test.csv")}
        resp = client.post("/api/preview", data=data, content_type="multipart/form-data")
        result = resp.get_json()
        assert resp.status_code == 200
        assert result["success"] is True
        assert result["data"]["total_rows"] == 2
        assert "columns" in result["data"]

    def test_no_file(self, client):
        resp = client.post("/api/preview")
        result = resp.get_json()
        assert resp.status_code == 400
        assert result["success"] is False

    def test_empty_file(self, client):
        data = {"file": (io.BytesIO(b""), "empty.csv")}
        resp = client.post("/api/preview", data=data, content_type="multipart/form-data")
        result = resp.get_json()
        assert resp.status_code == 400
        assert result["success"] is False

    def test_unsupported_extension(self, client):
        data = {"file": (io.BytesIO(b"data"), "test.txt")}
        resp = client.post("/api/preview", data=data, content_type="multipart/form-data")
        result = resp.get_json()
        assert resp.status_code == 400
        assert "Unsupported" in result["error"]["message"]

    def test_malformed_csv(self, client):
        data = {"file": (io.BytesIO(b'"""broken""",,\n'), "bad.csv")}
        resp = client.post("/api/preview", data=data, content_type="multipart/form-data")
        result = resp.get_json()
        assert "success" in result


class TestConvertEndpoint:
    def test_successful_conversion(self, client, sample_csv_bytes):
        file_id = _upload_first(client, sample_csv_bytes)

        payload = {
            "file_id": file_id,
            "orientation": "records",
            "indent": 2,
            "null_handling": "keep",
            "type_detection": True,
            "minified": False,
            "duplicate_handling": "keep",
            "empty_row_handling": "remove_empty",
        }
        resp = client.post("/api/convert", json=payload)
        result = resp.get_json()
        assert resp.status_code == 200
        assert result["success"] is True
        assert "json_string" in result["data"]
        assert result["data"]["record_count"] == 2

        # Verify valid JSON
        parsed = json.loads(result["data"]["json_string"])
        assert isinstance(parsed, list)
        assert len(parsed) == 2

    def test_invalid_request_body(self, client):
        resp = client.post("/api/convert", data="not json", content_type="text/plain")
        result = resp.get_json()
        assert resp.status_code == 400

    def test_no_file_id(self, client):
        resp = client.post("/api/convert", json={})
        result = resp.get_json()
        assert resp.status_code == 400

    def test_invalid_file_id(self, client):
        payload = {"file_id": "nonexistent.csv"}
        resp = client.post("/api/convert", json=payload)
        result = resp.get_json()
        assert resp.status_code == 400

    def test_minified_output(self, client, sample_csv_bytes):
        file_id = _upload_first(client, sample_csv_bytes)
        payload = {
            "file_id": file_id,
            "orientation": "records",
            "indent": 2,
            "minified": True,
        }
        resp = client.post("/api/convert", json=payload)
        result = resp.get_json()
        assert result["success"] is True
        json_str = result["data"]["json_string"]
        assert "\n" not in json_str


class TestDownloadEndpoint:
    def test_download_success(self, client, sample_csv_bytes):
        file_id = _upload_first(client, sample_csv_bytes)
        payload = {"file_id": file_id, "orientation": "records", "indent": 2}
        resp = client.post("/api/convert", json=payload)
        result = resp.get_json()
        filename = result["data"]["output_filename"]

        resp = client.get(f"/api/download/{filename}")
        assert resp.status_code == 200
        assert resp.content_type == "application/json"

    def test_download_not_found(self, client):
        resp = client.get("/api/download/nonexistent.json")
        assert resp.status_code == 404

    def test_download_safe_filename(self, client):
        # Path traversal attempt — safe filename sanitizes it
        resp = client.get("/api/download/../../etc/passwd.json")
        # After sanitization, the file won't exist in output dir
        assert resp.status_code == 404


class Test404:
    def test_unknown_route(self, client):
        resp = client.get("/api/nonexistent")
        assert resp.status_code == 404
