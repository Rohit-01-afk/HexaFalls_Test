"""
Unit tests for PromptBuilder context preparation, formatting, whitespace normalization,
structured prompt rendering, recovery prompt construction, prompt versioning, and intent-aware instructions.
"""

import pytest
from backend.schemas.query_intent import QueryIntent, QueryIntentType
from backend.schemas.search import SearchResult
from backend.services.evidence_service import EvidencePreparer
from backend.services.prompt_builder import PROMPT_VERSION, Prompt, PromptBuilder, SYSTEM_PROMPT


def test_prompt_builder_version() -> None:
    """Verify prompt version identifier is updated to 2.1."""
    assert PROMPT_VERSION == "2.1"
    assert PromptBuilder.PROMPT_VERSION == "2.1"


def test_prompt_builder_immutability() -> None:
    """Verify Prompt object is an immutable frozen dataclass containing pure structured data."""
    prompt = Prompt(system="Sys", context="Ctx", user="User Question", intent=QueryIntentType.PROCEDURE)
    assert prompt.system == "Sys"
    assert prompt.context == "Ctx"
    assert prompt.user == "User Question"
    assert prompt.intent == QueryIntentType.PROCEDURE
    assert prompt.is_recovery is False

    with pytest.raises(Exception):
        prompt.system = "Modified System"  # type: ignore[misc]


def test_prompt_builder_recovery_prompt() -> None:
    """Verify build_recovery_prompt constructs a lightweight recovery prompt."""
    chunks = [SearchResult(document_id="d1", chunk_id="c1", page_number=1, score=0.9, text="Recovery text")]
    prompt = PromptBuilder.build_recovery_prompt("Question?", chunks)
    assert prompt.is_recovery is True
    rendered = PromptBuilder.render_prompt(prompt)
    assert "DOCUMENT" in rendered
    assert "QUESTION" in rendered
    assert "ANSWER" in rendered


def test_prompt_builder_evidence_section_formatting() -> None:
    """Verify context formatting includes PRIMARY EVIDENCE and SUPPORTING EVIDENCE section headers when both exist."""
    chunks = [
        SearchResult(document_id="d1", chunk_id="c1", page_number=1, score=0.95, text="Top primary chunk"),
        SearchResult(document_id="d1", chunk_id="c2", page_number=2, score=0.60, text="Lower supporting chunk"),
    ]

    evidence = EvidencePreparer.prepare_evidence(chunks)
    prompt = PromptBuilder.build_prompt("Question?", evidence, include_page_headers=True)

    assert "[PRIMARY EVIDENCE]" in prompt.context
    assert "[SUPPORTING EVIDENCE]" in prompt.context
    assert "Page 1" in prompt.context
    assert "Page 2" in prompt.context


def test_prompt_builder_render_prompt_structured() -> None:
    """Verify render_prompt produces structured section headers."""
    chunks = [
        SearchResult(
            document_id="doc-101",
            chunk_id="chunk-01",
            page_number=82,
            score=0.71,
            text="Step 1: Turn off the main circuit breaker.",
        )
    ]
    prompt = PromptBuilder.build_prompt("How to isolate power?", chunks, include_page_headers=True)
    rendered = PromptBuilder.render_prompt(prompt)

    assert "DOCUMENT" in rendered
    assert "QUESTION" in rendered
    assert "ANSWER" in rendered
    assert "How to isolate power?" in rendered
    assert "Page 82" in rendered



def test_prompt_builder_count_context_blocks() -> None:
    """Verify count_context_blocks dynamically computes block count derived from context."""
    chunks = [
        SearchResult(document_id="d1", chunk_id="c1", page_number=1, score=0.9, text="Block 1 content"),
        SearchResult(document_id="d1", chunk_id="c2", page_number=2, score=0.8, text="Block 2 content"),
    ]
    prompt = PromptBuilder.build_prompt("Test question", chunks)
    assert PromptBuilder.count_context_blocks(prompt.context) > 0
    assert PromptBuilder.count_context_blocks("") == 0
