"""
Service layer for LLM answer response validation.
ResponseValidator verifies generated answer text quality before returning payloads or triggering retry decisions.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from backend.core.config import settings
from backend.core.logging import logger


class ValidationReason(str, Enum):
    """Specific failure or success reasons for response validation."""

    VALID = "valid"
    EMPTY = "empty"
    WHITESPACE_ONLY = "whitespace_only"
    PUNCTUATION_ONLY = "punctuation_only"
    MALFORMED_OUTPUT = "malformed_output"


@dataclass(frozen=True)
class ValidationResult:
    """
    Structured validation output containing status, failure reason, and answer character length.

    Attributes:
        valid: True if response passed validation, False otherwise.
        reason: ValidationReason status code.
        response_length: Total character count of evaluated response string.
    """

    valid: bool
    reason: ValidationReason
    response_length: int


class ResponseValidator:
    """
    Responsible ONLY for response validation.
    Must NOT perform retrieval or modify prompts.
    """

    @classmethod
    def validate_response(
        cls,
        answer: Optional[str],
        generation_id: Optional[str] = None,
    ) -> ValidationResult:
        """
        Evaluates answer string for quality anomalies (empty, whitespace, punctuation, malformed output).

        Args:
            answer: Raw or trimmed generated answer string from LLM.
            generation_id: Optional unique generation identifier for tracing.

        Returns:
            ValidationResult dataclass model.
        """
        gen_id = generation_id or "gen-unknown"

        def _log_result(res: ValidationResult) -> ValidationResult:
            if getattr(settings, "DEBUG_RAG_PIPELINE", False):
                logger.info(
                    "\n===== RESPONSE VALIDATION =====\n\nGeneration ID: %s\nValidation status: %s\nValidation reason: %s\nResponse length: %d\n",
                    gen_id,
                    res.valid,
                    res.reason.value if hasattr(res.reason, "value") else str(res.reason),
                    res.response_length,
                )
            return res

        if answer is None or len(answer) == 0:
            return _log_result(ValidationResult(valid=False, reason=ValidationReason.EMPTY, response_length=0))

        raw_length = len(answer)
        stripped = answer.strip()

        if len(stripped) == 0:
            return _log_result(ValidationResult(valid=False, reason=ValidationReason.WHITESPACE_ONLY, response_length=raw_length))

        # Detect punctuation-only string (no alphanumeric characters)
        alphanumeric_chars = re.sub(r"[^\w]", "", stripped, flags=re.UNICODE)
        if len(alphanumeric_chars) == 0:
            return _log_result(ValidationResult(valid=False, reason=ValidationReason.PUNCTUATION_ONLY, response_length=raw_length))

        # Detect malformed outputs (extremely short non-meaningful string under 2 alphanumeric chars)
        if len(alphanumeric_chars) < 2 and stripped not in ["no", "N/A", "ok"]:
            return _log_result(ValidationResult(valid=False, reason=ValidationReason.MALFORMED_OUTPUT, response_length=raw_length))

        return _log_result(ValidationResult(valid=True, reason=ValidationReason.VALID, response_length=raw_length))

