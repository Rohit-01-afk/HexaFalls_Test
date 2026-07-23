"""
Service layer responsible for HTTP communication with Ollama LLM provider.
"""

import time
from typing import Any, Dict
import httpx

from backend.core.config import settings
from backend.core.exceptions import (
    OllamaConnectionError,
    OllamaResponseError,
    OllamaTimeoutError,
)
from backend.core.logging import logger
from backend.services.prompt_builder import Prompt


class OllamaService:
    """Communicates directly with local Ollama service for text generation."""

    @classmethod
    async def generate_answer(cls, prompt: Prompt) -> str:
        """
        Formats prompt for Ollama API, executes HTTP POST request, measures latency,
        and returns parsed generated answer text.

        Args:
            prompt: Immutable Prompt model.

        Returns:
            Generated text string response from Ollama.

        Raises:
            OllamaTimeoutError: If HTTP request times out.
            OllamaConnectionError: If connection to Ollama fails.
            OllamaResponseError: If Ollama returns non-200 or invalid payload.
        """
        endpoint = f"{settings.OLLAMA_HOST.rstrip('/')}/api/generate"

        formatted_user_prompt = (
            f"Context:\n{prompt.context}\n\n"
            f"Question: {prompt.user}"
        )

        payload: Dict[str, Any] = {
            "model": settings.OLLAMA_MODEL,
            "system": prompt.system,
            "prompt": formatted_user_prompt,
            "stream": False,
        }

        start_time = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
                response = await client.post(endpoint, json=payload)
        except httpx.TimeoutException as err:
            latency = time.perf_counter() - start_time
            logger.warning("Ollama request timed out after %.3f seconds: %s", latency, str(err))
            raise OllamaTimeoutError("Generation timed out while communicating with Ollama server.") from err
        except (httpx.ConnectError, httpx.NetworkError) as err:
            latency = time.perf_counter() - start_time
            logger.warning("Ollama connection failed after %.3f seconds: %s", latency, str(err))
            raise OllamaConnectionError("Ollama service is unavailable.") from err
        except Exception as err:
            latency = time.perf_counter() - start_time
            logger.error("Unexpected error connecting to Ollama after %.3f seconds: %s", latency, str(err))
            raise OllamaConnectionError("Ollama service is unavailable.") from err

        latency = time.perf_counter() - start_time
        logger.info("Ollama response received in %.3f seconds (status=%d)", latency, response.status_code)

        if response.status_code != 200:
            logger.error("Ollama API error response status %d: %s", response.status_code, response.text)
            raise OllamaResponseError("Ollama returned a malformed response.")

        try:
            data = response.json()
            answer = data.get("response")
            if answer is None:
                raise ValueError("Missing 'response' field in payload")
            return str(answer).strip()
        except Exception as err:
            logger.error("Failed to parse JSON response from Ollama: %s", str(err))
            raise OllamaResponseError("Ollama returned a malformed response.") from err
