"""
Service layer responsible for HTTP communication with Google Gemini REST API.
"""

import time
from typing import Any, Dict, Optional
import httpx

from backend.core.config import settings
from backend.core.exceptions import (
    GeminiConnectionError,
    GeminiResponseError,
    GeminiTimeoutError,
)
from backend.core.logging import logger, write_debug_file
from backend.services.prompt_builder import PROMPT_VERSION, Prompt, PromptBuilder


class GeminiService:
    """Communicates directly with Google Gemini API for RAG text generation."""

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
        Formats prompt via PromptBuilder, executes HTTP POST request to Google Gemini API with configurable parameters,
        logs diagnostic lifecycle metrics (Started, Completed, Failed), and returns parsed generated text.
        """
        import os
        from dotenv import load_dotenv

        api_key = settings.GEMINI_API_KEY
        if not api_key:
            load_dotenv(override=True)
            api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            logger.error("Gemini API call failed: GEMINI_API_KEY is not configured")
            raise GeminiConnectionError("Gemini API key is not configured.")

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={api_key}"
        rendered_prompt = PromptBuilder.render_prompt(prompt)
        block_count = PromptBuilder.count_context_blocks(prompt.context)
        gen_id = generation_id or "gen-unknown"
        phase_label = "Retry" if is_retry else "Generation"

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [
                        {"text": rendered_prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": settings.GEMINI_TEMPERATURE,
                "topP": settings.GEMINI_TOP_P,
                "maxOutputTokens": settings.GEMINI_MAX_OUTPUT_TOKENS,
            },
        }

        if prompt.system:
            payload["system_instruction"] = {
                "parts": [
                    {"text": prompt.system}
                ]
            }

        if options:
            payload["generationConfig"].update(options)

        # Log generation lifecycle: Started
        logger.info(
            "Gemini %s started (gen_id=%s): model=%s, version=%s, timeout=%.1fs, prompt_chars=%d, context_chars=%d, raw_chunks=%d, filtered_chunks=%d, primary_evidence=%d, supporting_evidence=%d, context_blocks=%d",
            phase_label,
            gen_id,
            settings.GEMINI_MODEL,
            PROMPT_VERSION,
            settings.GEMINI_TIMEOUT,
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
                f"===== GEMINI REQUEST =====\n\n"
                f"Generation ID: {gen_id}\n"
                f"Model: {settings.GEMINI_MODEL}\n"
                f"System prompt length: {len(prompt.system)}\n"
                f"Rendered prompt length: {len(rendered_prompt)}\n\n"
                f"Rendered prompt:\n"
                f"{rendered_prompt}\n"
            )
            write_debug_file("gemini_request.txt", req_debug_content)

        start_time = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=settings.GEMINI_TIMEOUT) as client:
                response = await client.post(endpoint, json=payload)
        except httpx.TimeoutException as err:
            latency = time.perf_counter() - start_time
            logger.error(
                "Gemini %s failed (gen_id=%s): model=%s, version=%s, timeout=%.1fs, latency=%.3fs, error=Timeout: %s",
                phase_label,
                gen_id,
                settings.GEMINI_MODEL,
                PROMPT_VERSION,
                settings.GEMINI_TIMEOUT,
                latency,
                str(err),
            )
            raise GeminiTimeoutError("Generation timed out while communicating with Gemini API.") from err
        except (httpx.ConnectError, httpx.NetworkError) as err:
            latency = time.perf_counter() - start_time
            logger.error(
                "Gemini %s failed (gen_id=%s): model=%s, version=%s, timeout=%.1fs, latency=%.3fs, error=Connection failed: %s",
                phase_label,
                gen_id,
                settings.GEMINI_MODEL,
                PROMPT_VERSION,
                settings.GEMINI_TIMEOUT,
                latency,
                str(err),
            )
            raise GeminiConnectionError("Gemini API service is unavailable.") from err
        except Exception as err:
            latency = time.perf_counter() - start_time
            logger.error(
                "Gemini %s failed (gen_id=%s): model=%s, version=%s, timeout=%.1fs, latency=%.3fs, error=Unexpected: %s",
                phase_label,
                gen_id,
                settings.GEMINI_MODEL,
                PROMPT_VERSION,
                settings.GEMINI_TIMEOUT,
                latency,
                str(err),
            )
            raise GeminiConnectionError("Gemini API service is unavailable.") from err

        latency = time.perf_counter() - start_time

        if response.status_code != 200:
            logger.error(
                "Gemini %s failed (gen_id=%s): model=%s, version=%s, timeout=%.1fs, latency=%.3fs, error=HTTP status %d: %s",
                phase_label,
                gen_id,
                settings.GEMINI_MODEL,
                PROMPT_VERSION,
                settings.GEMINI_TIMEOUT,
                latency,
                response.status_code,
                response.text,
            )
            raise GeminiResponseError(f"Gemini API returned status {response.status_code}: {response.text}")

        try:
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("Missing 'candidates' in Gemini response payload")

            content_parts = candidates[0].get("content", {}).get("parts", [])
            if not content_parts or "text" not in content_parts[0]:
                raise ValueError("Missing 'parts[0].text' in Gemini candidate content")

            answer_str = str(content_parts[0]["text"]).strip()

            if getattr(settings, "DEBUG_RAG_PIPELINE", False):
                resp_debug_content = (
                    f"===== GEMINI RAW RESPONSE =====\n\n"
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
                write_debug_file("gemini_response.txt", resp_debug_content)

            # Log generation lifecycle: Completed
            logger.info(
                "Gemini %s completed (gen_id=%s): model=%s, version=%s, timeout=%.1fs, latency=%.3fs, prompt_chars=%d, context_chars=%d, raw_chunks=%d, filtered_chunks=%d, primary_evidence=%d, supporting_evidence=%d, context_blocks=%d, status=%d",
                phase_label,
                gen_id,
                settings.GEMINI_MODEL,
                PROMPT_VERSION,
                settings.GEMINI_TIMEOUT,
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
                "Gemini %s failed (gen_id=%s): model=%s, version=%s, timeout=%.1fs, latency=%.3fs, error=Parse error: %s",
                phase_label,
                gen_id,
                settings.GEMINI_MODEL,
                PROMPT_VERSION,
                settings.GEMINI_TIMEOUT,
                latency,
                str(err),
            )
            raise GeminiResponseError("Gemini returned a malformed response.") from err
