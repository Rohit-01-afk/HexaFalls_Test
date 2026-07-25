"""
Service layer responsible for HTTP communication with Ollama LLM provider.
"""

import time
from typing import Any, Dict, Optional
import httpx

from backend.core.config import settings
from backend.core.exceptions import (
    OllamaConnectionError,
    OllamaResponseError,
    OllamaTimeoutError,
)
from backend.core.logging import logger, write_debug_file
from backend.services.prompt_builder import PROMPT_VERSION, Prompt, PromptBuilder


class OllamaService:
    """Communicates directly with local Ollama service for text generation."""

    @classmethod
    async def generate_answer(
        cls,
        prompt: Prompt,
        raw_chunk_count: int = 0,
        filtered_chunk_count: int = 0,
        primary_evidence_count: int = 0,
        supporting_evidence_count: int = 0,
        generation_id: Optional[str] = None,
        is_retry: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Formats prompt via PromptBuilder, executes HTTP POST request to Ollama API with configurable parameters,
        logs diagnostic lifecycle metrics (Started, Completed, Failed), and returns parsed generated text.
        """
        endpoint = f"{settings.OLLAMA_HOST.rstrip('/')}/api/generate"
        rendered_prompt = PromptBuilder.render_prompt(prompt)
        block_count = PromptBuilder.count_context_blocks(prompt.context)
        gen_id = generation_id or "gen-unknown"
        phase_label = "Retry" if is_retry else "Generation"


        # Build configurable generation options payload
        options_payload: Dict[str, Any] = {
            "temperature": settings.OLLAMA_TEMPERATURE,
            "top_p": settings.OLLAMA_TOP_P,
            "num_predict": settings.OLLAMA_NUM_PREDICT,
            "repeat_penalty": settings.OLLAMA_REPEAT_PENALTY,
        }
        if settings.OLLAMA_SEED is not None:
            options_payload["seed"] = settings.OLLAMA_SEED
        if options:
            options_payload.update(options)

        payload: Dict[str, Any] = {
            "model": settings.OLLAMA_MODEL,
            "system": prompt.system,
            "prompt": rendered_prompt,
            "stream": False,
            "options": options_payload,
        }

        # Log generation lifecycle: Started
        logger.info(
            "Ollama %s started (gen_id=%s): model=%s, version=%s, timeout=%.1fs, prompt_chars=%d, context_chars=%d, raw_chunks=%d, filtered_chunks=%d, primary_evidence=%d, supporting_evidence=%d, context_blocks=%d",
            phase_label,
            gen_id,
            settings.OLLAMA_MODEL,
            PROMPT_VERSION,
            settings.OLLAMA_TIMEOUT,
            len(rendered_prompt),
            len(prompt.context),
            raw_chunk_count,
            filtered_chunk_count,
            primary_evidence_count,
            supporting_evidence_count,
            block_count,
        )

        if getattr(settings, "DEBUG_RAG_PIPELINE", False):
            req_debug_content = (
                f"===== OLLAMA REQUEST =====\n\n"
                f"Generation ID: {gen_id}\n"
                f"Endpoint: {endpoint}\n"
                f"Model: {settings.OLLAMA_MODEL}\n"
                f"Generation options: {options_payload}\n"
                f"System prompt length: {len(prompt.system)}\n"
                f"Rendered prompt length: {len(rendered_prompt)}\n\n"
                f"Rendered prompt:\n"
                f"{rendered_prompt}\n"
            )
            write_debug_file("ollama_request.txt", req_debug_content)


        start_time = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
                response = await client.post(endpoint, json=payload)
        except httpx.TimeoutException as err:
            latency = time.perf_counter() - start_time
            logger.error(
                "Ollama %s failed (gen_id=%s): model=%s, version=%s, timeout=%.1fs, latency=%.3fs, error=Timeout: %s",
                phase_label,
                gen_id,
                settings.OLLAMA_MODEL,
                PROMPT_VERSION,
                settings.OLLAMA_TIMEOUT,
                latency,
                str(err),
            )
            raise OllamaTimeoutError("Generation timed out while communicating with Ollama server.") from err
        except (httpx.ConnectError, httpx.NetworkError) as err:
            latency = time.perf_counter() - start_time
            logger.error(
                "Ollama %s failed (gen_id=%s): model=%s, version=%s, timeout=%.1fs, latency=%.3fs, error=Connection failed: %s",
                phase_label,
                gen_id,
                settings.OLLAMA_MODEL,
                PROMPT_VERSION,
                settings.OLLAMA_TIMEOUT,
                latency,
                str(err),
            )
            raise OllamaConnectionError("Ollama service is unavailable.") from err
        except Exception as err:
            latency = time.perf_counter() - start_time
            logger.error(
                "Ollama %s failed (gen_id=%s): model=%s, version=%s, timeout=%.1fs, latency=%.3fs, error=Unexpected: %s",
                phase_label,
                gen_id,
                settings.OLLAMA_MODEL,
                PROMPT_VERSION,
                settings.OLLAMA_TIMEOUT,
                latency,
                str(err),
            )
            raise OllamaConnectionError("Ollama service is unavailable.") from err

        latency = time.perf_counter() - start_time

        if response.status_code != 200:
            logger.error(
                "Ollama %s failed (gen_id=%s): model=%s, version=%s, timeout=%.1fs, latency=%.3fs, error=HTTP status %d",
                phase_label,
                gen_id,
                settings.OLLAMA_MODEL,
                PROMPT_VERSION,
                settings.OLLAMA_TIMEOUT,
                latency,
                response.status_code,
            )
            raise OllamaResponseError("Ollama returned a malformed response.")

        try:
            data = response.json()
            answer = data.get("response")
            if answer is None:
                raise ValueError("Missing 'response' field in payload")

            answer_str = str(answer).strip()

            if getattr(settings, "DEBUG_RAG_PIPELINE", False):
                resp_debug_content = (
                    f"===== OLLAMA RAW RESPONSE =====\n\n"
                    f"Generation ID: {gen_id}\n\n"
                    f"{response.text}\n\n"
                    f"===== RAW GENERATED ANSWER =====\n\n"
                    f"Generation ID: {gen_id}\n\n"
                    f"{answer_str}\n\n"
                    f"===== GENERATION SUMMARY =====\n\n"
                    f"Generation ID: {gen_id}\n"
                    f"Latency: {latency:.3f}s\n"
                    f"Answer length: {len(answer_str)}\n"
                    f"First 100 characters of answer: {answer_str[:100]}\n"
                )
                write_debug_file("ollama_response.txt", resp_debug_content)

            # Log generation lifecycle: Completed
            logger.info(
                "Ollama %s completed (gen_id=%s): model=%s, version=%s, timeout=%.1fs, latency=%.3fs, prompt_chars=%d, context_chars=%d, raw_chunks=%d, filtered_chunks=%d, primary_evidence=%d, supporting_evidence=%d, context_blocks=%d, status=%d",
                phase_label,
                gen_id,
                settings.OLLAMA_MODEL,
                PROMPT_VERSION,
                settings.OLLAMA_TIMEOUT,
                latency,
                len(rendered_prompt),
                len(prompt.context),
                raw_chunk_count,
                filtered_chunk_count,
                primary_evidence_count,
                supporting_evidence_count,
                block_count,
                response.status_code,
            )
            return answer_str
        except Exception as err:
            logger.error(
                "Ollama %s failed (gen_id=%s): model=%s, version=%s, timeout=%.1fs, latency=%.3fs, error=Parse error: %s",
                phase_label,
                gen_id,
                settings.OLLAMA_MODEL,
                PROMPT_VERSION,
                settings.OLLAMA_TIMEOUT,
                latency,
                str(err),
            )
            raise OllamaResponseError("Ollama returned a malformed response.") from err
