"""
Unit tests for Semantic Search Engine endpoint and service.
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
from backend.services.embedding_service import EmbeddingService

client = TestClient(app)


def test_search_empty_query() -> None:
    """Test 400 response when query is empty."""
    response = client.post("/api/v1/search", json={"query": ""})
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == 400
    assert "empty or whitespace" in data["error"].lower()


def test_search_whitespace_query() -> None:
    """Test 400 response when query is whitespace-only."""
    response = client.post("/api/v1/search", json={"query": "    \t \n "})
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == 400
    assert "empty or whitespace" in data["error"].lower()


def test_search_invalid_top_k() -> None:
    """Test 400 response when top_k is out of bounds (< 1 or > MAX_TOP_K)."""
    # top_k = 0
    res_zero = client.post("/api/v1/search", json={"query": "cooling fan", "top_k": 0})
    assert res_zero.status_code == 400

    # top_k = 50 (exceeding MAX_TOP_K 20)
    res_excess = client.post("/api/v1/search", json={"query": "cooling fan", "top_k": 50})
    assert res_excess.status_code == 400


def test_search_no_results_empty_collection(tmp_path: Path, monkeypatch) -> None:
    """Test 200 response returning empty results list when collection has no documents."""
    chroma_dir = tmp_path / "chromadb"
    chroma_dir.mkdir()

    monkeypatch.setattr(settings, "CHROMA_PATH", str(chroma_dir))

    response = client.post("/api/v1/search", json={"query": "how do I replace cooling fan?"})

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "how do I replace cooling fan?"
    assert data["count"] == 0
    assert data["results"] == []


def test_search_successful_multi_doc(tmp_path: Path, monkeypatch) -> None:
    """Test successful semantic search across multiple indexed documents."""
    chunk_dir = tmp_path / "chunks"
    chroma_dir = tmp_path / "chromadb"
    chunk_dir.mkdir()
    chroma_dir.mkdir()

    monkeypatch.setattr(settings, "CHUNK_STORAGE_PATH", str(chunk_dir))
    monkeypatch.setattr(settings, "CHROMA_PATH", str(chroma_dir))

    doc1_id = str(uuid.uuid4())
    doc2_id = str(uuid.uuid4())

    chunk1_data = {
        "document_id": doc1_id,
        "total_chunks": 1,
        "chunks": [
            {
                "chunk_id": str(uuid.uuid4()),
                "document_id": doc1_id,
                "page_number": 18,
                "text": "Disconnect cable J7 before removing the cooling fan assembly from the rear chassis.",
                "start_char": 0,
                "end_char": 84,
                "token_count": 13,
            }
        ],
    }

    chunk2_data = {
        "document_id": doc2_id,
        "total_chunks": 1,
        "chunks": [
            {
                "chunk_id": str(uuid.uuid4()),
                "document_id": doc2_id,
                "page_number": 5,
                "text": "Inspect main power supply fuse F1 for continuity during annual maintenance.",
                "start_char": 0,
                "end_char": 75,
                "token_count": 11,
            }
        ],
    }

    (chunk_dir / f"{doc1_id}.json").write_text(json.dumps(chunk1_data), encoding="utf-8")
    (chunk_dir / f"{doc2_id}.json").write_text(json.dumps(chunk2_data), encoding="utf-8")

    # Embed both documents into ChromaDB
    res1 = client.post(f"/api/v1/embed/{doc1_id}")
    assert res1.status_code == 200
    res2 = client.post(f"/api/v1/embed/{doc2_id}")
    assert res2.status_code == 200

    # Execute search query targeting cooling fan
    response = client.post("/api/v1/search", json={"query": "how to replace cooling fan", "top_k": 5})

    assert response.status_code == 200
    data = response.json()

    assert data["query"] == "how to replace cooling fan"
    assert data["count"] == 2
    assert len(data["results"]) == 2

    # Top result should be doc1 containing cooling fan text
    top_result = data["results"][0]
    assert top_result["document_id"] == doc1_id
    assert top_result["page_number"] == 18
    assert "cooling fan" in top_result["text"].lower()
    assert top_result["score"] > 0.0


def test_search_ordering_and_top_k_limit(tmp_path: Path, monkeypatch) -> None:
    """Test result sorting order (score descending) and top_k count limiting."""
    chunk_dir = tmp_path / "chunks"
    chroma_dir = tmp_path / "chromadb"
    chunk_dir.mkdir()
    chroma_dir.mkdir()

    monkeypatch.setattr(settings, "CHUNK_STORAGE_PATH", str(chunk_dir))
    monkeypatch.setattr(settings, "CHROMA_PATH", str(chroma_dir))

    doc_id = str(uuid.uuid4())

    chunk_data = {
        "document_id": doc_id,
        "total_chunks": 3,
        "chunks": [
            {
                "chunk_id": str(uuid.uuid4()),
                "document_id": doc_id,
                "page_number": 1,
                "text": "Unscrew the four mounting bolts to replace the thermal cooling fan.",
                "start_char": 0,
                "end_char": 66,
                "token_count": 11,
            },
            {
                "chunk_id": str(uuid.uuid4()),
                "document_id": doc_id,
                "page_number": 2,
                "text": "The hydraulic pump system operates at 3000 PSI nominal pressure.",
                "start_char": 0,
                "end_char": 64,
                "token_count": 9,
            },
            {
                "chunk_id": str(uuid.uuid4()),
                "document_id": doc_id,
                "page_number": 3,
                "text": "Cooling system maintenance requires checking fan motor rotational speed.",
                "start_char": 0,
                "end_char": 71,
                "token_count": 9,
            },
        ],
    }

    (chunk_dir / f"{doc_id}.json").write_text(json.dumps(chunk_data), encoding="utf-8")

    # Embed document into ChromaDB
    embed_res = client.post(f"/api/v1/embed/{doc_id}")
    assert embed_res.status_code == 200

    # Search with top_k = 2 limit
    response = client.post("/api/v1/search", json={"query": "cooling fan maintenance", "top_k": 2})

    assert response.status_code == 200
    data = response.json()

    assert data["count"] == 2
    results = data["results"]
    assert len(results) == 2

    # Verify score descending order: results[0].score >= results[1].score
    assert results[0]["score"] >= results[1]["score"]
