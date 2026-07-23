"""
Unit tests for Chunk Generation Engine endpoint and service.
"""

import json
from pathlib import Path
from fastapi.testclient import TestClient
from backend.core.config import settings
from backend.main import app

client = TestClient(app)


def test_chunk_single_page(tmp_path: Path, monkeypatch) -> None:
    """Test chunking a single-page document."""
    meta_dir = tmp_path / "metadata"
    chunk_dir = tmp_path / "chunks"
    meta_dir.mkdir()
    chunk_dir.mkdir()

    monkeypatch.setattr(settings, "METADATA_STORAGE_PATH", str(meta_dir))
    monkeypatch.setattr(settings, "CHUNK_STORAGE_PATH", str(chunk_dir))

    doc_id = "doc_single_123"
    meta_file = meta_dir / f"{doc_id}.json"

    meta_content = {
        "document_id": doc_id,
        "total_pages": 1,
        "pages": [
            {
                "page_id": "p1",
                "document_id": doc_id,
                "page_number": 1,
                "image_path": "storage/page_images/doc_single_123/page_1.png",
                "text": "This is a single page manual text for chunking testing.",
            }
        ],
    }
    meta_file.write_text(json.dumps(meta_content), encoding="utf-8")

    response = client.post(f"/api/v1/chunk/{doc_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["document_id"] == doc_id
    assert data["chunks"] == 1
    assert data["status"] == "chunked"

    saved_chunk_file = chunk_dir / f"{doc_id}.json"
    assert saved_chunk_file.exists()

    chunks_json = json.loads(saved_chunk_file.read_text(encoding="utf-8"))
    assert chunks_json["document_id"] == doc_id
    assert chunks_json["total_chunks"] == 1
    assert len(chunks_json["chunks"]) == 1
    assert chunks_json["chunks"][0]["page_number"] == 1


def test_chunk_multi_page(tmp_path: Path, monkeypatch) -> None:
    """Test chunking a multi-page document preserving page numbers."""
    meta_dir = tmp_path / "metadata"
    chunk_dir = tmp_path / "chunks"
    meta_dir.mkdir()
    chunk_dir.mkdir()

    monkeypatch.setattr(settings, "METADATA_STORAGE_PATH", str(meta_dir))
    monkeypatch.setattr(settings, "CHUNK_STORAGE_PATH", str(chunk_dir))

    doc_id = "doc_multi_456"
    meta_file = meta_dir / f"{doc_id}.json"

    meta_content = {
        "document_id": doc_id,
        "total_pages": 3,
        "pages": [
            {"page_id": "p1", "document_id": doc_id, "page_number": 1, "image_path": "", "text": "Page 1 text content"},
            {"page_id": "p2", "document_id": doc_id, "page_number": 2, "image_path": "", "text": "Page 2 text content"},
            {"page_id": "p3", "document_id": doc_id, "page_number": 3, "image_path": "", "text": "Page 3 text content"},
        ],
    }
    meta_file.write_text(json.dumps(meta_content), encoding="utf-8")

    response = client.post(f"/api/v1/chunk/{doc_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["chunks"] == 3

    saved_chunk_file = chunk_dir / f"{doc_id}.json"
    chunks_json = json.loads(saved_chunk_file.read_text(encoding="utf-8"))
    chunks = chunks_json["chunks"]

    assert len(chunks) == 3
    assert chunks[0]["page_number"] == 1
    assert chunks[1]["page_number"] == 2
    assert chunks[2]["page_number"] == 3


def test_chunk_missing_metadata(tmp_path: Path, monkeypatch) -> None:
    """Test 404 response when metadata file does not exist."""
    meta_dir = tmp_path / "metadata"
    meta_dir.mkdir()

    monkeypatch.setattr(settings, "METADATA_STORAGE_PATH", str(meta_dir))

    response = client.post("/api/v1/chunk/non_existent_doc_id")
    assert response.status_code == 404
    data = response.json()
    assert data["status"] == 404
    assert "not found" in data["error"].lower()


def test_chunk_empty_metadata(tmp_path: Path, monkeypatch) -> None:
    """Test 400 response when metadata JSON has no pages."""
    meta_dir = tmp_path / "metadata"
    meta_dir.mkdir()

    monkeypatch.setattr(settings, "METADATA_STORAGE_PATH", str(meta_dir))

    doc_id = "doc_empty_meta"
    meta_file = meta_dir / f"{doc_id}.json"
    meta_file.write_text(json.dumps({"document_id": doc_id, "pages": []}), encoding="utf-8")

    response = client.post(f"/api/v1/chunk/{doc_id}")
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == 400
    assert "no pages" in data["error"].lower()


def test_chunk_short_text(tmp_path: Path, monkeypatch) -> None:
    """Test text shorter than CHUNK_SIZE producing 1 chunk."""
    meta_dir = tmp_path / "metadata"
    chunk_dir = tmp_path / "chunks"
    meta_dir.mkdir()
    chunk_dir.mkdir()

    monkeypatch.setattr(settings, "METADATA_STORAGE_PATH", str(meta_dir))
    monkeypatch.setattr(settings, "CHUNK_STORAGE_PATH", str(chunk_dir))
    monkeypatch.setattr(settings, "CHUNK_SIZE", 500)

    doc_id = "doc_short"
    short_text = "Short sentence text."
    meta_file = meta_dir / f"{doc_id}.json"
    meta_file.write_text(
        json.dumps({"document_id": doc_id, "pages": [{"page_number": 1, "text": short_text}]}),
        encoding="utf-8",
    )

    response = client.post(f"/api/v1/chunk/{doc_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["chunks"] == 1


def test_chunk_long_text_and_overlap_correctness(tmp_path: Path, monkeypatch) -> None:
    """Test long text sliding window chunking and character overlap accuracy."""
    meta_dir = tmp_path / "metadata"
    chunk_dir = tmp_path / "chunks"
    meta_dir.mkdir()
    chunk_dir.mkdir()

    monkeypatch.setattr(settings, "METADATA_STORAGE_PATH", str(meta_dir))
    monkeypatch.setattr(settings, "CHUNK_STORAGE_PATH", str(chunk_dir))
    monkeypatch.setattr(settings, "CHUNK_SIZE", 500)
    monkeypatch.setattr(settings, "CHUNK_OVERLAP", 100)

    doc_id = "doc_long"
    # Create 1200 character text (A, B, C... repeating)
    page_text = "".join([f"Word{i:04d} " for i in range(150)])  # ~1350 chars
    meta_file = meta_dir / f"{doc_id}.json"
    meta_file.write_text(
        json.dumps({"document_id": doc_id, "pages": [{"page_number": 1, "text": page_text}]}),
        encoding="utf-8",
    )

    response = client.post(f"/api/v1/chunk/{doc_id}")
    assert response.status_code == 200

    saved_file = chunk_dir / f"{doc_id}.json"
    chunks_data = json.loads(saved_file.read_text(encoding="utf-8"))["chunks"]

    # Verify multiple chunks generated
    assert len(chunks_data) > 1

    # Verify overlap correctness between consecutive chunks
    chunk0 = chunks_data[0]
    chunk1 = chunks_data[1]

    # Overlap region: end of chunk0 should match start of chunk1
    overlap_len = 100
    chunk0_tail = chunk0["text"][-overlap_len:]
    chunk1_head = chunk1["text"][:overlap_len]

    assert chunk0_tail == chunk1_head


def test_chunk_offset_correctness(tmp_path: Path, monkeypatch) -> None:
    """Test character start_char and end_char offset correctness against page text."""
    meta_dir = tmp_path / "metadata"
    chunk_dir = tmp_path / "chunks"
    meta_dir.mkdir()
    chunk_dir.mkdir()

    monkeypatch.setattr(settings, "METADATA_STORAGE_PATH", str(meta_dir))
    monkeypatch.setattr(settings, "CHUNK_STORAGE_PATH", str(chunk_dir))
    monkeypatch.setattr(settings, "CHUNK_SIZE", 300)
    monkeypatch.setattr(settings, "CHUNK_OVERLAP", 50)

    doc_id = "doc_offset"
    page_text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" * 30  # 1080 chars
    meta_file = meta_dir / f"{doc_id}.json"
    meta_file.write_text(
        json.dumps({"document_id": doc_id, "pages": [{"page_number": 1, "text": page_text}]}),
        encoding="utf-8",
    )

    response = client.post(f"/api/v1/chunk/{doc_id}")
    assert response.status_code == 200

    saved_file = chunk_dir / f"{doc_id}.json"
    chunks_data = json.loads(saved_file.read_text(encoding="utf-8"))["chunks"]

    for chunk in chunks_data:
        start = chunk["start_char"]
        end = chunk["end_char"]
        expected_text = page_text[start:end]
        assert chunk["text"] == expected_text
