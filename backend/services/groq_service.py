"""
Service layer responsible for HTTP communication with Groq REST API (Llama 3.3 / Llama 3.1).
"""

import os
import time
from typing import Any, Dict, Optional
import httpx
from dotenv import load_dotenv

from backend.core.config import settings
from backend.core.exceptions import (
    GroqConnectionError,
    GroqResponseError,
    GroqTimeoutError,
)
from backend.core.logging import logger, write_debug_file
from backend.services.prompt_builder import PROMPT_VERSION, Prompt, PromptBuilder


class GroqService:
    """Communicates directly with Groq API for ultra-fast RAG text generation."""

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
        Formats prompt via PromptBuilder, executes HTTP POST request to Groq API,
        logs diagnostic metrics, and returns generated text.
        """
        api_key = settings.GROQ_API_KEY
        if not api_key:
            load_dotenv(override=True)
            api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            logger.error("Groq API call failed: GROQ_API_KEY is not configured")
            raise GroqConnectionError("Groq API key is not configured. Please add GROQ_API_KEY to your .env file.")

        endpoint = "https://api.groq.com/openai/v1/chat/completions"
        rendered_prompt = PromptBuilder.render_prompt(prompt)
        block_count = PromptBuilder.count_context_blocks(prompt.context)
        gen_id = generation_id or "gen-unknown"
        phase_label = "Retry" if is_retry else "Generation"

        messages = []
        if prompt.system:
            messages.append({"role": "system", "content": prompt.system})
        messages.append({"role": "user", "content": rendered_prompt})

        model_name = settings.GROQ_MODEL or "llama-3.3-70b-versatile"

        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": settings.GROQ_TEMPERATURE,
            "top_p": settings.GROQ_TOP_P,
            "max_tokens": settings.GROQ_MAX_OUTPUT_TOKENS,
        }

        if options:
            payload.update(options)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Log generation lifecycle: Started
        logger.info(
            "Groq %s started (gen_id=%s): model=%s, version=%s, timeout=%.1fs, prompt_chars=%d, context_chars=%d, raw_chunks=%d, filtered_chunks=%d, primary_evidence=%d, supporting_evidence=%d, context_blocks=%d",
            phase_label,
            gen_id,
            model_name,
            PROMPT_VERSION,
            settings.GROQ_TIMEOUT,
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
                f"===== GROQ REQUEST =====\n\n"
                f"Generation ID: {gen_id}\n"
                f"Model: {model_name}\n"
                f"System prompt length: {len(prompt.system)}\n"
                f"Rendered prompt length: {len(rendered_prompt)}\n\n"
                f"Rendered prompt:\n"
                f"{rendered_prompt}\n"
            )
            write_debug_file("groq_request.txt", req_debug_content)

        start_time = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=settings.GROQ_TIMEOUT) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
        except httpx.TimeoutException as err:
            latency = time.perf_counter() - start_time
            logger.error(
                "Groq %s failed (gen_id=%s): model=%s, latency=%.3fs, error=Timeout: %s",
                phase_label,
                gen_id,
                model_name,
                latency,
                str(err),
            )
            raise GroqTimeoutError("Generation timed out while communicating with Groq API.") from err
        except (httpx.ConnectError, httpx.NetworkError) as err:
            latency = time.perf_counter() - start_time
            logger.error(
                "Groq %s failed (gen_id=%s): model=%s, latency=%.3fs, error=Connection failed: %s",
                phase_label,
                gen_id,
                model_name,
                latency,
                str(err),
            )
            raise GroqConnectionError("Groq API service is unavailable.") from err
        except Exception as err:
            latency = time.perf_counter() - start_time
            logger.error(
                "Groq %s failed (gen_id=%s): model=%s, latency=%.3fs, error=Unexpected: %s",
                phase_label,
                gen_id,
                model_name,
                latency,
                str(err),
            )
            raise GroqConnectionError("Groq API service is unavailable.") from err

        latency = time.perf_counter() - start_time

        if response.status_code != 200:
            logger.error(
                "Groq %s failed (gen_id=%s): model=%s, latency=%.3fs, error=HTTP status %d: %s",
                phase_label,
                gen_id,
                model_name,
                latency,
                response.status_code,
                response.text,
            )
            raise GroqResponseError(f"Groq API returned status {response.status_code}: {response.text}")

        try:
            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                raise ValueError("Missing 'choices' in Groq response payload")

            message_obj = choices[0].get("message", {})
            answer_str = str(message_obj.get("content", "")).strip()

            if getattr(settings, "DEBUG_RAG_PIPELINE", False):
                resp_debug_content = (
                    f"===== GROQ RAW RESPONSE =====\n\n"
                    f"Generation ID: {gen_id}\n\n"
                    f"{response.text}\n\n"
                    f"===== RAW GENERATED ANSWER =====\n\n"
                    f"Generation ID: {gen_id}\n\n"
                    f"{answer_str}\n"
                )
                write_debug_file("groq_response.txt", resp_debug_content)

            # Log generation lifecycle: Completed
            logger.info(
                "Groq %s completed (gen_id=%s): model=%s, version=%s, timeout=%.1fs, latency=%.3fs, prompt_chars=%d, context_chars=%d, status=%d",
                phase_label,
                gen_id,
                model_name,
                PROMPT_VERSION,
                settings.GROQ_TIMEOUT,
                latency,
                len(rendered_prompt),
                len(prompt.context),
                response.status_code,
            )
            return answer_str
        except Exception as err:
            logger.error(
                "Groq %s failed (gen_id=%s): model=%s, latency=%.3fs, error=Parse error: %s",
                phase_label,
                gen_id,
                model_name,
                latency,
                str(err),
            )
            raise GroqResponseError("Groq returned a malformed response.") from err
