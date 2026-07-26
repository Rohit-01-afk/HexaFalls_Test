"""
Unit tests for GeminiService generation and error handling.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from backend.services.gemini_service import GeminiService
from backend.services.prompt_builder import PromptBuilder, Prompt
from backend.core.exceptions import (
    GeminiConnectionError,
    GeminiResponseError,
    GeminiTimeoutError,
)
import httpx


@pytest.mark.anyio
async def test_gemini_service_generate_answer_success() -> None:
    """Test successful Gemini API text generation."""
    test_prompt = Prompt(
        system="You are a manual assistant.",
        context="Spec: 100 PSI",
        user="What is the pressure rating?",
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"candidates": [{"content": {"parts": [{"text": "The pressure rating is 100 PSI."}]}}]}'
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "The pressure rating is 100 PSI."}]
                }
            }
        ]
    }

    with patch("backend.services.gemini_service.settings.GEMINI_API_KEY", "test-api-key"):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            answer = await GeminiService.generate_answer(test_prompt)
            assert answer == "The pressure rating is 100 PSI."


@pytest.mark.anyio
async def test_gemini_service_missing_api_key() -> None:
    """Test GeminiService error when GEMINI_API_KEY is not set."""
    test_prompt = Prompt(
        system="",
        context="",
        user="Test question",
    )
    with patch("backend.services.gemini_service.settings.GEMINI_API_KEY", None), \
         patch("os.getenv", return_value=None):
        with pytest.raises(GeminiConnectionError, match="Gemini API key is not configured"):
            await GeminiService.generate_answer(test_prompt)


@pytest.mark.anyio
async def test_gemini_service_timeout() -> None:
    """Test GeminiService timeout handling."""
    test_prompt = Prompt(system="", context="", user="Test question")
    with patch("backend.services.gemini_service.settings.GEMINI_API_KEY", "test-api-key"):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Timeout")
            with pytest.raises(GeminiTimeoutError):
                await GeminiService.generate_answer(test_prompt)


@pytest.mark.anyio
async def test_gemini_service_non_200_response() -> None:
    """Test GeminiService response error on non-200 status code."""
    test_prompt = Prompt(system="", context="", user="Test question")
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"

    with patch("backend.services.gemini_service.settings.GEMINI_API_KEY", "test-api-key"):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(GeminiResponseError):
                await GeminiService.generate_answer(test_prompt)
