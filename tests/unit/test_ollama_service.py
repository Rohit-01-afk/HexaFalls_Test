"""
Unit tests for OllamaService communication, payload configuration, timeout handling, and diagnostic logging.
"""

from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest

from backend.core.config import settings
from backend.core.exceptions import (
    OllamaConnectionError,
    OllamaResponseError,
    OllamaTimeoutError,
)
from backend.schemas.query_intent import QueryIntentType
from backend.services.ollama_service import OllamaService
from backend.services.prompt_builder import PROMPT_VERSION, Prompt, PromptBuilder


@pytest.fixture
def sample_prompt() -> Prompt:
    return Prompt(
        system="System prompt instructions",
        context="Page 10\nSample manual context text.",
        user="How do I service the pump?",
        intent=QueryIntentType.PROCEDURE,
    )


@pytest.mark.anyio
async def test_ollama_service_successful_generation(sample_prompt: Prompt) -> None:
    """Verify OllamaService formats payload with generation options and returns response text."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "Turn off power before servicing pump."}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        answer = await OllamaService.generate_answer(
            sample_prompt,
            raw_chunk_count=5,
            filtered_chunk_count=3,
        )

        assert answer == "Turn off power before servicing pump."
        assert mock_post.called

        # Inspect call payload
        call_kwargs = mock_post.call_args.kwargs
        json_payload = call_kwargs["json"]
        assert json_payload["model"] == settings.OLLAMA_MODEL
        assert json_payload["system"] == sample_prompt.system
        assert json_payload["stream"] is False
        assert "DOCUMENT" in json_payload["prompt"]

        options = json_payload["options"]
        assert options["temperature"] == settings.OLLAMA_TEMPERATURE
        assert options["top_p"] == settings.OLLAMA_TOP_P
        assert options["num_predict"] == settings.OLLAMA_NUM_PREDICT
        assert options["repeat_penalty"] == settings.OLLAMA_REPEAT_PENALTY
        assert options["seed"] == settings.OLLAMA_SEED


@pytest.mark.anyio
async def test_ollama_service_timeout_handling(sample_prompt: Prompt) -> None:
    """Verify OllamaService catches httpx.TimeoutException and raises OllamaTimeoutError."""
    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timeout after 120s")):
        with pytest.raises(OllamaTimeoutError):
            await OllamaService.generate_answer(sample_prompt)


@pytest.mark.anyio
async def test_ollama_service_connection_error_handling(sample_prompt: Prompt) -> None:
    """Verify OllamaService catches connection errors and raises OllamaConnectionError."""
    request_mock = httpx.Request("POST", "http://localhost:11434/api/generate")
    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused", request=request_mock)):
        with pytest.raises(OllamaConnectionError):
            await OllamaService.generate_answer(sample_prompt)


@pytest.mark.anyio
async def test_ollama_service_non_200_response(sample_prompt: Prompt) -> None:
    """Verify OllamaService handles non-200 HTTP response codes."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        with pytest.raises(OllamaResponseError):
            await OllamaService.generate_answer(sample_prompt)


@pytest.mark.anyio
async def test_ollama_service_lifecycle_logging(sample_prompt: Prompt) -> None:
    """Verify OllamaService emits Generation Started and Generation Completed diagnostic logs."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "Clean answer response."}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, patch(
        "backend.services.ollama_service.logger.info"
    ) as mock_log_info:
        mock_post.return_value = mock_response

        await OllamaService.generate_answer(
            sample_prompt,
            raw_chunk_count=10,
            filtered_chunk_count=4,
        )

        assert mock_log_info.call_count >= 2
        start_log_msg = mock_log_info.call_args_list[0][0][0]
        completed_log_msg = mock_log_info.call_args_list[1][0][0]

        assert "started" in start_log_msg.lower()
        assert "completed" in completed_log_msg.lower()
