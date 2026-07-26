"""
Unit tests for RecoveryHandler retry orchestration and fallback handling.
"""

from unittest.mock import AsyncMock, patch
import pytest

from backend.schemas.search import SearchResult
from backend.services.evidence_service import EvidencePreparer
from backend.services.recovery_handler import RecoveryHandler, RecoveryResult
from backend.services.response_validator import ResponseValidator, ValidationReason, ValidationResult


@pytest.fixture
def sample_evidence():
    chunks = [
        SearchResult(document_id="d1", chunk_id="c1", page_number=5, score=0.85, text="Disconnect power harness W-100.")
    ]
    return EvidencePreparer.prepare_evidence(chunks)


@pytest.mark.anyio
async def test_recovery_handler_successful_retry(sample_evidence) -> None:
    """Verify RecoveryHandler requests recovery prompt from PromptBuilder and returns recovered answer."""
    gen_id = "gen-test-123"
    initial_val = ValidationResult(valid=False, reason=ValidationReason.EMPTY, response_length=0)

    with patch("backend.services.groq_service.GroqService.generate_answer", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "Disconnect power harness W-100."

        res = await RecoveryHandler.attempt_recovery(
            generation_id=gen_id,
            question="How to disconnect power?",
            evidence=sample_evidence,
            initial_validation=initial_val,
        )

        assert isinstance(res, RecoveryResult)
        assert res.recovered is True
        assert res.answer == "Disconnect power harness W-100."
        assert res.retry_used is True
        assert res.validation.valid is True


@pytest.mark.anyio
async def test_recovery_handler_failed_retry_reverts_to_fallback(sample_evidence) -> None:
    """Verify RecoveryHandler reverts to standard fallback if retry also fails validation."""
    gen_id = "gen-test-456"
    initial_val = ValidationResult(valid=False, reason=ValidationReason.PUNCTUATION_ONLY, response_length=3)

    with patch("backend.services.groq_service.GroqService.generate_answer", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "..."  # Still invalid punctuation

        res = await RecoveryHandler.attempt_recovery(
            generation_id=gen_id,
            question="Unknown procedure?",
            evidence=sample_evidence,
            initial_validation=initial_val,
        )

        assert isinstance(res, RecoveryResult)
        assert res.recovered is False
        assert res.answer == "I could not find this information in the manual."
        assert res.retry_used is True
