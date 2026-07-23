"""
Unit tests for PDF Processing Engine endpoint and service.
"""

import json
from pathlib import Path
import fitz  # PyMuPDF
from fastapi.testclient import TestClient
from backend.core.config import settings
from backend.main import app

client = TestClient(app)


def test_process_valid_pdf(tmp_path: Path, monkeypatch) -> None:
    """Test processing a valid single-page PDF document."""
    manuals_dir = tmp_path / "manuals"
    images_dir = tmp_path / "page_images"
    metadata_dir = tmp_path / "metadata"

    manuals_dir.mkdir()
    images_dir.mkdir()
    metadata_dir.mkdir()

    monkeypatch.setattr(settings, "MANUAL_STORAGE_PATH", str(manuals_dir))
    monkeypatch.setattr(settings, "PAGE_IMAGE_STORAGE_PATH", str(images_dir))
    monkeypatch.setattr(settings, "METADATA_STORAGE_PATH", str(metadata_dir))

    doc_id = "doc_valid_123"
    pdf_file = manuals_dir / f"{doc_id}_test_manual.pdf"

    # Create dummy 1-page PDF with text
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Technical Manual Page 1 Content")
    doc.save(str(pdf_file))
    doc.close()

    response = client.post(f"/api/v1/process/{doc_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["document_id"] == doc_id
    assert data["pages"] == 1
    assert data["status"] == "processed"

    # Verify rendered image file exists
    image_file = images_dir / doc_id / "page_1.png"
    assert image_file.exists()

    # Verify metadata JSON exists and content matches
    meta_file = metadata_dir / f"{doc_id}.json"
    assert meta_file.exists()

    meta_content = json.loads(meta_file.read_text(encoding="utf-8"))
    assert meta_content["document_id"] == doc_id
    assert meta_content["total_pages"] == 1
    assert len(meta_content["pages"]) == 1
    assert "Technical Manual Page 1 Content" in meta_content["pages"][0]["text"]


def test_process_multi_page_pdf(tmp_path: Path, monkeypatch) -> None:
    """Test processing a multi-page PDF document."""
    manuals_dir = tmp_path / "manuals"
    images_dir = tmp_path / "page_images"
    metadata_dir = tmp_path / "metadata"

    manuals_dir.mkdir()
    images_dir.mkdir()
    metadata_dir.mkdir()

    monkeypatch.setattr(settings, "MANUAL_STORAGE_PATH", str(manuals_dir))
    monkeypatch.setattr(settings, "PAGE_IMAGE_STORAGE_PATH", str(images_dir))
    monkeypatch.setattr(settings, "METADATA_STORAGE_PATH", str(metadata_dir))

    doc_id = "doc_multipage_456"
    pdf_file = manuals_dir / f"{doc_id}_multi_manual.pdf"

    # Create dummy 3-page PDF
    doc = fitz.open()
    for i in range(3):
        p = doc.new_page()
        p.insert_text((50, 50), f"Page {i + 1} Instructions")
    doc.save(str(pdf_file))
    doc.close()

    response = client.post(f"/api/v1/process/{doc_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["document_id"] == doc_id
    assert data["pages"] == 3
    assert data["status"] == "processed"

    # Verify 3 page images created
    for page_num in range(1, 4):
        image_file = images_dir / doc_id / f"page_{page_num}.png"
        assert image_file.exists()


def test_process_missing_pdf(tmp_path: Path, monkeypatch) -> None:
    """Test 404 response when document_id does not exist."""
    manuals_dir = tmp_path / "manuals"
    manuals_dir.mkdir()

    monkeypatch.setattr(settings, "MANUAL_STORAGE_PATH", str(manuals_dir))

    response = client.post("/api/v1/process/non_existent_doc_id")

    assert response.status_code == 404
    data = response.json()
    assert data["status"] == 404
    assert "not found" in data["error"].lower()


def test_process_corrupted_pdf(tmp_path: Path, monkeypatch) -> None:
    """Test 400 response when PDF file is corrupted."""
    manuals_dir = tmp_path / "manuals"
    manuals_dir.mkdir()

    monkeypatch.setattr(settings, "MANUAL_STORAGE_PATH", str(manuals_dir))

    doc_id = "doc_corrupted_789"
    corrupted_file = manuals_dir / f"{doc_id}_corrupted.pdf"
    corrupted_file.write_bytes(b"NOT A VALID PDF FILE CONTENT")

    response = client.post(f"/api/v1/process/{doc_id}")

    assert response.status_code == 400
    data = response.json()
    assert data["status"] == 400
    assert "corrupted" in data["error"].lower() or "invalid" in data["error"].lower()


def test_process_empty_pdf(tmp_path: Path, monkeypatch) -> None:
    """Test 400 response when PDF document contains 0 pages."""
    manuals_dir = tmp_path / "manuals"
    manuals_dir.mkdir()

    monkeypatch.setattr(settings, "MANUAL_STORAGE_PATH", str(manuals_dir))

    doc_id = "doc_empty_000"
    pdf_file = manuals_dir / f"{doc_id}_empty.pdf"

    # Write raw 0-page PDF content
    empty_pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Count 0 /Kids [] >>\nendobj\n"
        b"xref\n0 3\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n"
        b"trailer\n<< /Size 3 /Root 1 0 R >>\n"
        b"startxref\n115\n%%EOF"
    )
    pdf_file.write_bytes(empty_pdf_bytes)

    response = client.post(f"/api/v1/process/{doc_id}")

    assert response.status_code == 400
    data = response.json()
    assert data["status"] == 400
    assert "no pages" in data["error"].lower()
