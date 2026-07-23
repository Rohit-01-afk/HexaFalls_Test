"""
Unit tests for Retrieval-Augmented Generation (RAG) services, prompt builder, Ollama integration, and endpoint.
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
    OllamaConnectionError,
    OllamaResponseError,
    OllamaTimeoutError,
)
from backend.main import app
from backend.schemas.search import SearchResponse, SearchResult
from backend.services.ollama_service import OllamaService
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
    assert "[Page 18]\nDisconnect cable J7 before removing cooling fan." in prompt.context
    assert "[Page 19]\nUnscrew the four mounting bolts." in prompt.context


# --- 2. OllamaService Unit Tests ---


@pytest.mark.anyio
async def test_ollama_service_successful_generation() -> None:
    """Test successful answer generation from Ollama HTTP API."""
    prompt = Prompt(system="Sys", context="[Page 1]\nTest context", user="Test Q")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "Disconnect cable J7 completely."}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        answer = await OllamaService.generate_answer(prompt)

        assert answer == "Disconnect cable J7 completely."
        assert mock_post.called


@pytest.mark.anyio
async def test_ollama_service_timeout() -> None:
    """Test OllamaTimeoutError raised on httpx TimeoutException."""
    prompt = Prompt(system="Sys", context="Ctx", user="User Q")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Connection timed out")

        with pytest.raises(OllamaTimeoutError):
            await OllamaService.generate_answer(prompt)


@pytest.mark.anyio
async def test_ollama_service_connection_failure() -> None:
    """Test OllamaConnectionError raised on httpx ConnectError."""
    prompt = Prompt(system="Sys", context="Ctx", user="User Q")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(OllamaConnectionError):
            await OllamaService.generate_answer(prompt)


@pytest.mark.anyio
async def test_ollama_service_malformed_response() -> None:
    """Test OllamaResponseError raised on non-200 HTTP status or missing response field."""
    prompt = Prompt(system="Sys", context="Ctx", user="User Q")

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        with pytest.raises(OllamaResponseError):
            await OllamaService.generate_answer(prompt)


# --- 3. RAGService & API Endpoint Tests ---


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
        "backend.services.ollama_service.OllamaService.generate_answer", new_callable=AsyncMock
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
async def test_ask_ollama_service_unavailable_503() -> None:
    """Test 503 response when OllamaService raises OllamaConnectionError."""
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
        "backend.services.ollama_service.OllamaService.generate_answer", new_callable=AsyncMock
    ) as mock_gen:
        mock_search.return_value = mock_search_res
        mock_gen.side_effect = OllamaConnectionError("Ollama service is unavailable.")

        response = client.post("/api/v1/ask", json={"question": "cooling fan"})

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == 503
        assert "unavailable" in data["error"].lower()


@pytest.mark.anyio
async def test_ask_ollama_timeout_504() -> None:
    """Test 504 response when OllamaService raises OllamaTimeoutError."""
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
        "backend.services.ollama_service.OllamaService.generate_answer", new_callable=AsyncMock
    ) as mock_gen:
        mock_search.return_value = mock_search_res
        mock_gen.side_effect = OllamaTimeoutError("Generation timed out while communicating with Ollama server.")

        response = client.post("/api/v1/ask", json={"question": "cooling fan"})

        assert response.status_code == 504
        data = response.json()
        assert data["status"] == 504
        assert "timed out" in data["error"].lower()
