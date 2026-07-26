"""
Unit tests for GroqService (Groq API communication).
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from backend.core.exceptions import GroqConnectionError, GroqResponseError, GroqTimeoutError
from backend.services.groq_service import GroqService
from backend.services.prompt_builder import Prompt


@pytest.fixture
def mock_prompt():
    return Prompt(
        system="System prompt instruction",
        user="User question",
        context="Context details",
    )


@pytest.mark.anyio
async def test_groq_missing_api_key(mock_prompt):
    with patch("backend.core.config.settings.GROQ_API_KEY", None), \
         patch("os.getenv", return_value=None):
        with pytest.raises(GroqConnectionError) as exc_info:
            await GroqService.generate_answer(mock_prompt)
        assert "Groq API key is not configured" in str(exc_info.value)


@pytest.mark.anyio
async def test_groq_successful_generation(mock_prompt):
    mock_response_data = {
        "choices": [
            {
                "message": {
                    "content": "Gasket replacement is required every 10,000 miles."
                }
            }
        ]
    }

    mock_http_response = MagicMock()
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_response_data

    with patch("backend.core.config.settings.GROQ_API_KEY", "gsk_testkey123"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_http_response

        answer = await GroqService.generate_answer(mock_prompt)

        assert answer == "Gasket replacement is required every 10,000 miles."
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer gsk_testkey123"
        assert kwargs["json"]["model"] == "llama-3.3-70b-versatile"


@pytest.mark.anyio
async def test_groq_non_200_response(mock_prompt):
    mock_http_response = MagicMock()
    mock_http_response.status_code = 401
    mock_http_response.text = "Unauthorized API key"

    with patch("backend.core.config.settings.GROQ_API_KEY", "gsk_invalid"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_http_response

        with pytest.raises(GroqResponseError) as exc_info:
            await GroqService.generate_answer(mock_prompt)
        assert "401" in str(exc_info.value)
