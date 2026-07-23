"""
Unit tests for PDF manual upload endpoint and service.
"""

from pathlib import Path
from fastapi.testclient import TestClient
from backend.core.config import settings
from backend.main import app

client = TestClient(app)


def test_successful_pdf_upload(tmp_path: Path, monkeypatch) -> None:
    """Test successful PDF upload returning 201 Created and storing file."""
    monkeypatch.setattr(settings, "MANUAL_STORAGE_PATH", str(tmp_path))

    pdf_content = b"%PDF-1.4 sample PDF content line for testing"
    files = {"file": ("manual.pdf", pdf_content, "application/pdf")}

    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 201
    data = response.json()

    assert "document_id" in data
    assert data["filename"] == "manual.pdf"
    assert data["stored_filename"].endswith("_manual.pdf")
    assert data["size"] == len(pdf_content)
    assert data["status"] == "uploaded"

    stored_file = tmp_path / data["stored_filename"]
    assert stored_file.exists()
    assert stored_file.read_bytes() == pdf_content


def test_invalid_file_extension(tmp_path: Path, monkeypatch) -> None:
    """Test upload rejection when file extension is not .pdf."""
    monkeypatch.setattr(settings, "MANUAL_STORAGE_PATH", str(tmp_path))

    files = {"file": ("document.txt", b"plain text", "application/pdf")}
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 400
    data = response.json()
    assert data["status"] == 400
    assert "Invalid file extension" in data["error"]


def test_invalid_mime_type(tmp_path: Path, monkeypatch) -> None:
    """Test upload rejection when MIME type is not application/pdf."""
    monkeypatch.setattr(settings, "MANUAL_STORAGE_PATH", str(tmp_path))

    files = {"file": ("document.pdf", b"%PDF-1.4 content", "text/plain")}
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 400
    data = response.json()
    assert data["status"] == 400
    assert "Invalid MIME type" in data["error"]


def test_oversized_pdf_upload(tmp_path: Path, monkeypatch) -> None:
    """Test upload rejection when file size exceeds MAX_UPLOAD_SIZE_MB."""
    monkeypatch.setattr(settings, "MANUAL_STORAGE_PATH", str(tmp_path))
    # Set limit to 1 MB for test
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 1)

    # Generate oversized content (1.5 MB)
    oversized_content = b"%PDF-1.4 " + b"0" * (1 * 1024 * 1024 + 500)
    files = {"file": ("large_manual.pdf", oversized_content, "application/pdf")}

    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 413
    data = response.json()
    assert data["status"] == 413
    assert "File size exceeds maximum allowed limit" in data["error"]

    # Verify no file remains in storage directory
    stored_files = list(tmp_path.glob("*"))
    assert len(stored_files) == 0


def test_missing_file_upload() -> None:
    """Test 422 validation error when file parameter is omitted."""
    response = client.post("/api/v1/upload")
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == 422


def test_filename_sanitization(tmp_path: Path, monkeypatch) -> None:
    """Test filename sanitization preventing path traversal and unsafe chars."""
    monkeypatch.setattr(settings, "MANUAL_STORAGE_PATH", str(tmp_path))

    pdf_content = b"%PDF-1.4 content"
    files = {"file": ("../../etc/unsafe manual #1.pdf", pdf_content, "application/pdf")}

    response = client.post("/api/v1/upload", files=files)
    assert response.status_code == 201

    data = response.json()
    assert data["filename"] == "unsafe manual #1.pdf"
    assert ".." not in data["stored_filename"]
    assert "#" not in data["stored_filename"]
    assert (tmp_path / data["stored_filename"]).exists()
