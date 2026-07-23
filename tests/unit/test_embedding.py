"""
Unit tests for Embedding Generation and Vector Indexing Engine endpoint and service.
"""

import json
import re
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock

# Patch grpc if DLL load is blocked by AppLocker policy
try:
    import grpc  # noqa: F401
except (ImportError, Exception):
    mock_grpc = MagicMock()
    mock_grpc.__version__ = "1.65.0"
    sys.modules["grpc"] = mock_grpc

# Patch regex module if compiled _regex.pyd is blocked by AppLocker policy
try:
    import regex  # noqa: F401
except (ImportError, Exception):
    sys.modules["regex"] = re

import chromadb
from fastapi.testclient import TestClient
from backend.core.config import settings
from backend.main import app

client = TestClient(app)


def test_embed_invalid_uuid_format() -> None:
    """Test 400 response when document_id is not a valid UUID format."""
    response = client.post("/api/v1/embed/invalid_doc_id_string")
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == 400
    assert "invalid document_id format" in data["error"].lower()


def test_embed_missing_chunks(tmp_path: Path, monkeypatch) -> None:
    """Test 404 response when chunk data file does not exist."""
    chunk_dir = tmp_path / "chunks"
    chroma_dir = tmp_path / "chromadb"
    chunk_dir.mkdir()
    chroma_dir.mkdir()

    monkeypatch.setattr(settings, "CHUNK_STORAGE_PATH", str(chunk_dir))
    monkeypatch.setattr(settings, "CHROMA_PATH", str(chroma_dir))

    valid_uuid = str(uuid.uuid4())
    response = client.post(f"/api/v1/embed/{valid_uuid}")
    assert response.status_code == 404
    data = response.json()
    assert data["status"] == 404
    assert "not found" in data["error"].lower()


def test_embed_empty_chunks(tmp_path: Path, monkeypatch) -> None:
    """Test 400 response when chunk JSON contains 0 chunks."""
    chunk_dir = tmp_path / "chunks"
    chroma_dir = tmp_path / "chromadb"
    chunk_dir.mkdir()
    chroma_dir.mkdir()

    monkeypatch.setattr(settings, "CHUNK_STORAGE_PATH", str(chunk_dir))
    monkeypatch.setattr(settings, "CHROMA_PATH", str(chroma_dir))

    doc_id = str(uuid.uuid4())
    chunk_file = chunk_dir / f"{doc_id}.json"
    chunk_file.write_text(json.dumps({"document_id": doc_id, "chunks": []}), encoding="utf-8")

    response = client.post(f"/api/v1/embed/{doc_id}")
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == 400
    assert "no chunks" in data["error"].lower()


def test_embed_successful_indexing(tmp_path: Path, monkeypatch) -> None:
    """Test successful embedding generation and indexing into ChromaDB."""
    chunk_dir = tmp_path / "chunks"
    chroma_dir = tmp_path / "chromadb"
    chunk_dir.mkdir()
    chroma_dir.mkdir()

    monkeypatch.setattr(settings, "CHUNK_STORAGE_PATH", str(chunk_dir))
    monkeypatch.setattr(settings, "CHROMA_PATH", str(chroma_dir))

    doc_id = str(uuid.uuid4())
    chunk_file = chunk_dir / f"{doc_id}.json"

    chunk_data = {
        "document_id": doc_id,
        "total_chunks": 2,
        "chunks": [
            {
                "chunk_id": str(uuid.uuid4()),
                "document_id": doc_id,
                "page_number": 1,
                "text": "Disconnect the main power connector J1 before servicing the unit.",
                "start_char": 0,
                "end_char": 66,
                "token_count": 10,
            },
            {
                "chunk_id": str(uuid.uuid4()),
                "document_id": doc_id,
                "page_number": 2,
                "text": "Unscrew the four mounting bolts on the cooling fan module.",
                "start_char": 0,
                "end_char": 58,
                "token_count": 10,
            },
        ],
    }
    chunk_file.write_text(json.dumps(chunk_data), encoding="utf-8")

    response = client.post(f"/api/v1/embed/{doc_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["document_id"] == doc_id
    assert data["indexed_chunks"] == 2
    assert data["collection"] == settings.CHROMA_COLLECTION
    assert data["status"] == "indexed"


def test_embed_duplicate_indexing(tmp_path: Path, monkeypatch) -> None:
    """Test duplicate re-indexing of the same document updates vectors cleanly (upsert)."""
    chunk_dir = tmp_path / "chunks"
    chroma_dir = tmp_path / "chromadb"
    chunk_dir.mkdir()
    chroma_dir.mkdir()

    monkeypatch.setattr(settings, "CHUNK_STORAGE_PATH", str(chunk_dir))
    monkeypatch.setattr(settings, "CHROMA_PATH", str(chroma_dir))

    doc_id = str(uuid.uuid4())
    chunk_1_id = str(uuid.uuid4())
    chunk_2_id = str(uuid.uuid4())
    chunk_file = chunk_dir / f"{doc_id}.json"

    chunk_data = {
        "document_id": doc_id,
        "total_chunks": 2,
        "chunks": [
            {
                "chunk_id": chunk_1_id,
                "document_id": doc_id,
                "page_number": 1,
                "text": "First chunk text content.",
                "start_char": 0,
                "end_char": 25,
                "token_count": 4,
            },
            {
                "chunk_id": chunk_2_id,
                "document_id": doc_id,
                "page_number": 1,
                "text": "Second chunk text content.",
                "start_char": 20,
                "end_char": 46,
                "token_count": 4,
            },
        ],
    }
    chunk_file.write_text(json.dumps(chunk_data), encoding="utf-8")

    # First indexing run
    res1 = client.post(f"/api/v1/embed/{doc_id}")
    assert res1.status_code == 200

    # Second indexing run (duplicate)
    res2 = client.post(f"/api/v1/embed/{doc_id}")
    assert res2.status_code == 200
    assert res2.json()["indexed_chunks"] == 2

    # Verify collection count remains 2 (no duplicate IDs created)
    c_client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = c_client.get_collection(name=settings.CHROMA_COLLECTION)
    assert collection.count() == 2


def test_embed_metadata_persistence(tmp_path: Path, monkeypatch) -> None:
    """Test metadata attributes persistence in ChromaDB collection."""
    chunk_dir = tmp_path / "chunks"
    chroma_dir = tmp_path / "chromadb"
    chunk_dir.mkdir()
    chroma_dir.mkdir()

    monkeypatch.setattr(settings, "CHUNK_STORAGE_PATH", str(chunk_dir))
    monkeypatch.setattr(settings, "CHROMA_PATH", str(chroma_dir))

    doc_id = str(uuid.uuid4())
    chunk_id = str(uuid.uuid4())
    chunk_file = chunk_dir / f"{doc_id}.json"

    chunk_data = {
        "document_id": doc_id,
        "total_chunks": 1,
        "chunks": [
            {
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "page_number": 5,
                "text": "Metadata verification sentence for testing storage.",
                "start_char": 10,
                "end_char": 61,
                "token_count": 6,
            }
        ],
    }
    chunk_file.write_text(json.dumps(chunk_data), encoding="utf-8")

    response = client.post(f"/api/v1/embed/{doc_id}")
    assert response.status_code == 200

    # Verify retrieved record from ChromaDB
    c_client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = c_client.get_collection(name=settings.CHROMA_COLLECTION)
    results = collection.get(ids=[chunk_id], include=["metadatas", "documents"])

    assert len(results["ids"]) == 1
    assert results["documents"][0] == "Metadata verification sentence for testing storage."

    retrieved_meta = results["metadatas"][0]
    assert retrieved_meta["document_id"] == doc_id
    assert retrieved_meta["page_number"] == 5
    assert retrieved_meta["chunk_id"] == chunk_id
    assert retrieved_meta["start_char"] == 10
    assert retrieved_meta["end_char"] == 61
    assert retrieved_meta["token_count"] == 6
