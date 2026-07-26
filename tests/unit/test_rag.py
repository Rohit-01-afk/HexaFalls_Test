"""
Unit tests for Retrieval-Augmented Generation (RAG) services, prompt builder, Gemini integration, and endpoint.
"""

import json
import re
import sys
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

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

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.core.config import settings
from backend.core.exceptions import (
    GroqConnectionError,
    GroqResponseError,
    GroqTimeoutError,
)
from backend.main import app
from backend.schemas.search import SearchResponse, SearchResult
from backend.services.groq_service import GroqService
from backend.services.prompt_builder import Prompt, PromptBuilder, SYSTEM_PROMPT
from backend.services.rag_service import RAGService

client = TestClient(app)


# --- 1. PromptBuilder Unit Tests ---


def test_prompt_builder_immutability() -> None:
    """Verify Prompt object is an immutable frozen dataclass."""
    prompt = Prompt(system="Sys", context="Ctx", user="User Q")
    assert prompt.system == "Sys"
    assert prompt.context == "Ctx"
    assert prompt.user == "User Q"

    with pytest.raises(Exception):
        prompt.system = "New Sys"  # type: ignore[misc]


def test_prompt_builder_construction() -> None:
    """Verify PromptBuilder constructs system prompt, context with page numbers, and question."""
    chunks = [
        SearchResult(
            document_id="doc-1",
            chunk_id="chunk-1",
            page_number=18,
            score=0.95,
            text="Disconnect cable J7 before removing cooling fan.",
        ),
        SearchResult(
            document_id="doc-1",
            chunk_id="chunk-2",
            page_number=19,
            score=0.88,
            text="Unscrew the four mounting bolts.",
        ),
    ]

    prompt = PromptBuilder.build_prompt("How to remove cooling fan?", chunks)

    assert prompt.system == SYSTEM_PROMPT
    assert prompt.user == "How to remove cooling fan?"
    assert "==========\nPage 18\nSimilarity: 0.95\nContent:\nDisconnect cable J7 before removing cooling fan." in prompt.context
    assert "==========\nPage 19\nSimilarity: 0.88\nContent:\nUnscrew the four mounting bolts." in prompt.context


# --- 2. RAGService & API Endpoint Tests ---


def test_ask_empty_question_validation() -> None:
    """Test 422 Unprocessable Content response for empty or whitespace question."""
    res_empty = client.post("/api/v1/ask", json={"question": ""})
    assert res_empty.status_code == 422

    res_spaces = client.post("/api/v1/ask", json={"question": "   \n\t "})
    assert res_spaces.status_code == 422


@pytest.mark.anyio
async def test_ask_empty_retrieval_fallback() -> None:
    """Test 200 OK fallback response when SearchService returns 0 chunks."""
    mock_search_res = SearchResponse(query="unknown query", count=0, results=[])

    with patch("backend.services.search_service.SearchService.search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_search_res

        response = client.post("/api/v1/ask", json={"question": "unknown query"})

        assert response.status_code == 200
        data = response.json()
        assert data["question"] == "unknown query"
        assert data["answer"] == "I could not find this information in the manual."
        assert data["sources"] == []


@pytest.mark.anyio
async def test_ask_successful_rag_flow() -> None:
    """Test complete successful RAG endpoint flow."""
    doc_id = str(uuid.uuid4())
    chunk_id = str(uuid.uuid4())

    mock_search_res = SearchResponse(
        query="cooling fan",
        count=1,
        results=[
            SearchResult(
                document_id=doc_id,
                chunk_id=chunk_id,
                page_number=18,
                score=0.94,
                text="Disconnect cable J7 before removing cooling fan.",
            )
        ],
    )

    with patch("backend.services.search_service.SearchService.search", new_callable=AsyncMock) as mock_search, patch(
        "backend.services.groq_service.GroqService.generate_answer", new_callable=AsyncMock
    ) as mock_gen:
        mock_search.return_value = mock_search_res
        mock_gen.return_value = "To remove the cooling fan, first disconnect cable J7."

        response = client.post("/api/v1/ask", json={"question": "cooling fan"})

        assert response.status_code == 200
        data = response.json()
        assert data["question"] == "cooling fan"
        assert data["answer"] == "To remove the cooling fan, first disconnect cable J7."
        assert len(data["sources"]) == 1
        assert data["sources"][0]["page"] == 18
        assert data["sources"][0]["chunk_id"] == chunk_id
        assert data["sources"][0]["score"] == 0.94


@pytest.mark.anyio
async def test_ask_groq_service_unavailable_503() -> None:
    """Test 503 response when GroqService raises GroqConnectionError."""
    mock_search_res = SearchResponse(
        query="cooling fan",
        count=1,
        results=[
            SearchResult(
                document_id="doc-1",
                chunk_id="c-1",
                page_number=1,
                score=0.9,
                text="Fan text",
            )
        ],
    )

    with patch("backend.services.search_service.SearchService.search", new_callable=AsyncMock) as mock_search, patch(
        "backend.services.groq_service.GroqService.generate_answer", new_callable=AsyncMock
    ) as mock_gen:
        mock_search.return_value = mock_search_res
        mock_gen.side_effect = GroqConnectionError("Groq API service is unavailable.")

        response = client.post("/api/v1/ask", json={"question": "cooling fan"})

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == 503
        assert "unavailable" in data["error"].lower()


@pytest.mark.anyio
async def test_ask_groq_timeout_504() -> None:
    """Test 504 response when GroqService raises GroqTimeoutError."""
    mock_search_res = SearchResponse(
        query="cooling fan",
        count=1,
        results=[
            SearchResult(
                document_id="doc-1",
                chunk_id="c-1",
                page_number=1,
                score=0.9,
                text="Fan text",
            )
        ],
    )

    with patch("backend.services.search_service.SearchService.search", new_callable=AsyncMock) as mock_search, patch(
        "backend.services.groq_service.GroqService.generate_answer", new_callable=AsyncMock
    ) as mock_gen:
        mock_search.return_value = mock_search_res
        mock_gen.side_effect = GroqTimeoutError("Generation timed out while communicating with Groq API.")

        response = client.post("/api/v1/ask", json={"question": "cooling fan"})

        assert response.status_code == 504
        data = response.json()
        assert data["status"] == 504
        assert "timed out" in data["error"].lower()


@pytest.mark.anyio
async def test_ask_below_threshold_fallback_soft_disabled() -> None:
    """Test 200 OK threshold fallback response when all retrieved chunks are below soft threshold or soft threshold disabled."""
    mock_search_res = SearchResponse(
        query="obscure part",
        count=1,
        results=[
            SearchResult(
                document_id="doc-1",
                chunk_id="c-low",
                page_number=5,
                score=0.20,  # Far below threshold (0.45) and soft margin (0.45 - 0.05 = 0.40)
                text="Irrelevant text snippet.",
            )
        ],
    )

    with patch("backend.services.search_service.SearchService.search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_search_res

        response = client.post("/api/v1/ask", json={"question": "obscure part"})

        assert response.status_code == 200
        data = response.json()
        assert data["question"] == "obscure part"
        assert data["answer"] == "I could not find sufficiently relevant information in the manual."
        assert data["sources"] == []
        assert data["confidence"] == "None"
        assert data["diagnostics"]["filter_reason"] == "filtered_below_threshold"
        assert data["metrics"]["total_ms"] >= 0


@pytest.mark.anyio
async def test_ask_soft_threshold_fallback_success() -> None:
    """Test soft threshold retrieval fallback when best score is within configurable margin (0.40 - 0.45)."""
    doc_id = str(uuid.uuid4())
    chunk_id = str(uuid.uuid4())

    # Candidate chunk score 0.42 is below default RAG_SIMILARITY_THRESHOLD (0.45), but >= soft cutoff (0.40)
    mock_search_res = SearchResponse(
        query="marginal topic",
        count=1,
        results=[
            SearchResult(
                document_id=doc_id,
                chunk_id=chunk_id,
                page_number=42,
                score=0.42,
                text="Marginal procedure information text.",
            )
        ],
    )

    with patch("backend.services.search_service.SearchService.search", new_callable=AsyncMock) as mock_search, patch(
        "backend.services.groq_service.GroqService.generate_answer", new_callable=AsyncMock
    ) as mock_gen:
        mock_search.return_value = mock_search_res
        mock_gen.return_value = "Marginal procedure summary answer."

        response = client.post("/api/v1/ask", json={"question": "marginal topic"})

        assert response.status_code == 200
        data = response.json()
        assert data["question"] == "marginal topic"
        assert data["answer"] == "Marginal procedure summary answer."
        assert data["confidence"] == "Low"
        assert len(data["sources"]) == 1
        assert data["sources"][0]["page"] == 42
        assert data["sources"][0]["score"] == 0.42
        assert data["sources"][0]["document_id"] == doc_id


@pytest.mark.anyio
async def test_ask_soft_threshold_disabled_behavior() -> None:
    """Test threshold fallback returned when soft threshold feature is toggled off."""
    mock_search_res = SearchResponse(
        query="marginal topic",
        count=1,
        results=[
            SearchResult(
                document_id="doc-1",
                chunk_id="c-1",
                page_number=42,
                score=0.42,
                text="Marginal procedure text.",
            )
        ],
    )

    with patch("backend.services.search_service.SearchService.search", new_callable=AsyncMock) as mock_search, patch(
        "backend.core.config.settings.RAG_ENABLE_SOFT_THRESHOLD", False
    ):
        mock_search.return_value = mock_search_res

        response = client.post("/api/v1/ask", json={"question": "marginal topic"})

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "I could not find sufficiently relevant information in the manual."
        assert data["confidence"] == "None"
        assert data["sources"] == []


@pytest.mark.anyio
async def test_ask_metrics_diagnostics_and_rich_metadata() -> None:
    """Test confidence, diagnostics, performance metrics, and rich source metadata in successful response."""
    doc_id = str(uuid.uuid4())
    chunk_id = str(uuid.uuid4())

    mock_search_res = SearchResponse(
        query="cooling fan assembly",
        count=1,
        results=[
            SearchResult(
                document_id=doc_id,
                chunk_id=chunk_id,
                page_number=18,
                score=0.92,
                text="Disconnect cable J7 before removing cooling fan.",
            )
        ],
    )

    with patch("backend.services.search_service.SearchService.search", new_callable=AsyncMock) as mock_search, patch(
        "backend.services.groq_service.GroqService.generate_answer", new_callable=AsyncMock
    ) as mock_gen:
        mock_search.return_value = mock_search_res
        mock_gen.return_value = "Unplug cable J7 first."

        response = client.post("/api/v1/ask", json={"question": "cooling fan assembly"})

        assert response.status_code == 200
        data = response.json()
        assert data["confidence"] == "High"
        assert data["diagnostics"]["returned_count"] == 1
        assert "search_ms" in data["metrics"]
        assert "filter_ms" in data["metrics"]
        assert "prompt_ms" in data["metrics"]
        assert "generation_ms" in data["metrics"]
        assert "total_ms" in data["metrics"]

        # Check rich source metadata
        source = data["sources"][0]
        assert source["document_id"] == doc_id
        assert "Disconnect cable J7" in source["preview"]


@pytest.mark.anyio
async def test_ask_with_document_id_filter() -> None:
    """Test POST /api/v1/ask forwards optional document_id filter to SearchService."""
    doc_id = str(uuid.uuid4())
    chunk_id = str(uuid.uuid4())

    mock_search_res = SearchResponse(
        query="Engineering Mathematics",
        count=1,
        results=[
            SearchResult(
                document_id=doc_id,
                chunk_id=chunk_id,
                page_number=14,
                score=0.91,
                text="Module I: Linear Algebra and Calculus.",
            )
        ],
    )

    with patch("backend.services.search_service.SearchService.search", new_callable=AsyncMock) as mock_search, patch(
        "backend.services.groq_service.GroqService.generate_answer", new_callable=AsyncMock
    ) as mock_gen:
        mock_search.return_value = mock_search_res
        mock_gen.return_value = "Engineering Mathematics-I covers Linear Algebra and Calculus."

        response = client.post("/api/v1/ask", json={"question": "Engineering Mathematics", "document_id": doc_id})

        assert response.status_code == 200
        data = response.json()
        assert data["question"] == "Engineering Mathematics"
        assert data["sources"][0]["document_id"] == doc_id

        # Verify SearchService.search was called with SearchRequest containing document_id
        called_req = mock_search.call_args[0][0]
        assert called_req.document_id == doc_id


@pytest.mark.anyio
async def test_ask_query_intent_diagnostics() -> None:
    """Test POST /api/v1/ask includes query intent diagnostics (intent, intent_confidence, matched_keywords, intent_reason)."""
    doc_id = str(uuid.uuid4())
    chunk_id = str(uuid.uuid4())

    mock_search_res = SearchResponse(
        query="How do I replace the cooling fan?",
        count=1,
        results=[
            SearchResult(
                document_id=doc_id,
                chunk_id=chunk_id,
                page_number=18,
                score=0.95,
                text="Disconnect cable J7 before replacing cooling fan.",
            )
        ],
    )

    with patch("backend.services.search_service.SearchService.search", new_callable=AsyncMock) as mock_search, patch(
        "backend.services.groq_service.GroqService.generate_answer", new_callable=AsyncMock
    ) as mock_gen:
        mock_search.return_value = mock_search_res
        mock_gen.return_value = "Disconnect cable J7 first."

        response = client.post("/api/v1/ask", json={"question": "How do I replace the cooling fan?"})

        assert response.status_code == 200
        data = response.json()
        assert "diagnostics" in data
        diag = data["diagnostics"]
        assert diag["intent"] == "procedure"
        assert diag["intent_confidence"] >= 0.85
        assert "how do i" in diag["matched_keywords"]
        assert "replace" in diag["matched_keywords"]
        assert "intent_reason" in diag
        assert "procedure" in diag["intent_reason"]
