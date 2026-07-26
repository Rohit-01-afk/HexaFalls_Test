"""
Service layer for automatic answer generation recovery and retry orchestration.
RecoveryHandler orchestrates single-attempt retries for invalid responses without building prompts.
"""

from dataclasses import dataclass
from typing import Optional, Type

from backend.core.config import settings
from backend.core.logging import logger
from backend.schemas.query_intent import QueryIntent
from backend.services.evidence_service import PreparedEvidence
from backend.services.groq_service import GroqService
from backend.services.prompt_builder import PromptBuilder
from backend.services.response_validator import ResponseValidator, ValidationResult

STANDARD_FALLBACK_ANSWER = "I could not find this information in the manual."


@dataclass(frozen=True)
class RecoveryResult:
    """
    Structured outcome of a recovery retry attempt.

    Attributes:
        recovered: True if retry produced a valid answer.
        answer: Final answer text (recovered answer or fallback).
        validation: ValidationResult model for the recovery answer.
        retry_used: True if retry attempt was executed.
    """

    recovered: bool
    answer: str
    validation: ValidationResult
    retry_used: bool


class RecoveryHandler:
    """
    Responsible ONLY for retry orchestration and recovery decision-making.
    Must NOT perform retrieval or build prompt text strings directly.
    """

    @classmethod
    async def attempt_recovery(
        cls,
        generation_id: str,
        question: str,
        evidence: PreparedEvidence,
        intent: Optional[QueryIntent] = None,
        initial_validation: Optional[ValidationResult] = None,
        raw_chunk_count: int = 0,
        filtered_chunk_count: int = 0,
        prompt_builder: Optional[Type[PromptBuilder]] = None,
        groq_service: Optional[Type[GroqService]] = None,
        response_validator: Optional[Type[ResponseValidator]] = None,
    ) -> RecoveryResult:
        """
        Executes an automatic recovery retry when initial generation fails validation.

        Args:
            generation_id: Unique generation identifier for tracing.
            question: User question string.
            evidence: PreparedEvidence model.
            intent: Optional QueryIntent classification metadata.
            initial_validation: ValidationResult from initial generation.
            raw_chunk_count: Raw chunk count before filtering.
            filtered_chunk_count: Filtered chunk count after filtering.
            prompt_builder: Optional PromptBuilder override.
            groq_service: Optional GroqService override.
            response_validator: Optional ResponseValidator override.

        Returns:
            RecoveryResult model.
        """
        prompt_cls = prompt_builder or PromptBuilder
        groq_cls = groq_service or GroqService
        validator_cls = response_validator or ResponseValidator

        max_retries = getattr(settings, "MAX_GENERATION_RETRIES", 1)
        initial_reason = initial_validation.reason.value if initial_validation else "unknown"

        if max_retries <= 0:
            logger.warning(
                "Generation %s recovery skipped: MAX_GENERATION_RETRIES=%d (initial_reason=%s)",
                generation_id,
                max_retries,
                initial_reason,
            )
            fallback_val = validator_cls.validate_response(STANDARD_FALLBACK_ANSWER)
            return RecoveryResult(
                recovered=False,
                answer=STANDARD_FALLBACK_ANSWER,
                validation=fallback_val,
                retry_used=False,
            )

        logger.info(
            "Generation %s retry started: initial_reason=%s, max_retries=%d",
            generation_id,
            initial_reason,
            max_retries,
        )

        if getattr(settings, "DEBUG_RAG_PIPELINE", False):
            logger.info("\n===== RECOVERY STARTED =====\n\nGeneration ID: %s\n", generation_id)

        # 1. Request lightweight recovery prompt from PromptBuilder
        recovery_prompt = prompt_cls.build_recovery_prompt(question, evidence, intent=intent, generation_id=generation_id)
        rendered_rec_prompt = prompt_cls.render_prompt(recovery_prompt, generation_id=generation_id)

        if getattr(settings, "DEBUG_RAG_PIPELINE", False):
            logger.info("\n===== RECOVERY PROMPT =====\n\nGeneration ID: %s\n\n%s\n", generation_id, rendered_rec_prompt)

        # 2. Execute retry generation call via GeminiService
        try:
            retry_answer = await groq_cls.generate_answer(
                recovery_prompt,
                raw_chunk_count=raw_chunk_count,
                filtered_chunk_count=filtered_chunk_count,
                primary_evidence_count=evidence.primary_count,
                supporting_evidence_count=evidence.supporting_count,
                generation_id=generation_id,
                is_retry=True,
            )
        except Exception as err:
            logger.error(
                "Generation %s retry failed during LLM call: error=%s",
                generation_id,
                str(err),
            )
            if getattr(settings, "DEBUG_RAG_PIPELINE", False):
                logger.info("\n===== RECOVERY DECISION =====\n\nGeneration ID: %s\n\nStandard Fallback\n", generation_id)
            fallback_val = validator_cls.validate_response(STANDARD_FALLBACK_ANSWER, generation_id=generation_id)
            return RecoveryResult(
                recovered=False,
                answer=STANDARD_FALLBACK_ANSWER,
                validation=fallback_val,
                retry_used=True,
            )

        if getattr(settings, "DEBUG_RAG_PIPELINE", False):
            logger.info("\n===== RECOVERY ANSWER =====\n\nGeneration ID: %s\n\n%s\n", generation_id, retry_answer)

        # 3. Validate retry response
        retry_validation = validator_cls.validate_response(retry_answer, generation_id=generation_id)

        if getattr(settings, "DEBUG_RAG_PIPELINE", False):
            logger.info(
                "\n===== RECOVERY VALIDATION =====\n\nGeneration ID: %s\n\nValidation result: %s\nReason: %s\n",
                generation_id,
                retry_validation.valid,
                retry_validation.reason.value if hasattr(retry_validation.reason, "value") else str(retry_validation.reason),
            )

        if retry_validation.valid:
            logger.info(
                "Generation %s retry completed successfully: answer_len=%d",
                generation_id,
                retry_validation.response_length,
            )
            if getattr(settings, "DEBUG_RAG_PIPELINE", False):
                logger.info("\n===== RECOVERY DECISION =====\n\nGeneration ID: %s\n\nRecovered\n", generation_id)
            return RecoveryResult(
                recovered=True,
                answer=retry_answer,
                validation=retry_validation,
                retry_used=True,
            )

        logger.warning(
            "Generation %s retry failed validation: reason=%s. Reverting to standard fallback.",
            generation_id,
            retry_validation.reason.value,
        )

        if getattr(settings, "DEBUG_RAG_PIPELINE", False):
            logger.info("\n===== RECOVERY DECISION =====\n\nGeneration ID: %s\n\nStandard Fallback\n", generation_id)

        fallback_val = validator_cls.validate_response(STANDARD_FALLBACK_ANSWER, generation_id=generation_id)
        return RecoveryResult(
            recovered=False,
            answer=STANDARD_FALLBACK_ANSWER,
            validation=fallback_val,
            retry_used=True,
        )
