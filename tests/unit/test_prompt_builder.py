"""
Unit tests for PromptBuilder context preparation, formatting, whitespace normalization,
deduplication, and system prompt compliance with Prompt Design Principles.
"""

import pytest
from backend.schemas.search import SearchResult
from backend.services.prompt_builder import Prompt, PromptBuilder, SYSTEM_PROMPT


def test_prompt_builder_immutability() -> None:
    """Verify Prompt object is an immutable frozen dataclass."""
    prompt = Prompt(system="Sys", context="Ctx", user="User Question")
    assert prompt.system == "Sys"
    assert prompt.context == "Ctx"
    assert prompt.user == "User Question"

    with pytest.raises(Exception):
        prompt.system = "Modified System"  # type: ignore[misc]


def test_system_prompt_design_principles() -> None:
    """Verify system prompt incorporates grounding, support distinction, and non-hallucination rules."""
    assert "Answer ONLY using the supplied manual context" in SYSTEM_PROMPT
    assert "Never use outside knowledge or fabricate information" in SYSTEM_PROMPT
    assert "Do NOT reveal internal reasoning, chain-of-thought" in SYSTEM_PROMPT
    assert 'reply exactly: "I could not find this information in the manual."' in SYSTEM_PROMPT
    assert "Preserve technical terminology" in SYSTEM_PROMPT


def test_prompt_builder_context_formatting_with_headers() -> None:
    """Verify context formatting includes delimiters, page number, similarity score, and content."""
    chunks = [
        SearchResult(
            document_id="doc-101",
            chunk_id="chunk-01",
            page_number=82,
            score=0.71,
            text="Step 1: Turn off the main circuit breaker.",
        ),
        SearchResult(
            document_id="doc-101",
            chunk_id="chunk-02",
            page_number=83,
            score=0.69,
            text="Step 2: Disconnect power wiring harness W-102.",
        ),
    ]

    prompt = PromptBuilder.build_prompt("How to isolate power?", chunks, include_page_headers=True)

    assert prompt.system == SYSTEM_PROMPT
    assert prompt.user == "How to isolate power?"
    assert "==========\nPage 82\nSimilarity: 0.71\nContent:\nStep 1: Turn off the main circuit breaker." in prompt.context
    assert "==========\nPage 83\nSimilarity: 0.69\nContent:\nStep 2: Disconnect power wiring harness W-102." in prompt.context


def test_prompt_builder_context_formatting_without_headers() -> None:
    """Verify context formatting when page headers toggle is disabled."""
    chunks = [
        SearchResult(
            document_id="doc-101",
            chunk_id="chunk-01",
            page_number=12,
            score=0.90,
            text="Check oil reservoir level.",
        )
    ]

    prompt = PromptBuilder.build_prompt("Oil check instructions", chunks, include_page_headers=False)

    assert "[Page 12]\nCheck oil reservoir level." in prompt.context
    assert "==========" not in prompt.context


def test_prompt_builder_empty_context() -> None:
    """Verify PromptBuilder gracefully handles empty chunk list."""
    prompt = PromptBuilder.build_prompt("Empty question", [])
    assert prompt.context == ""
    assert prompt.user == "Empty question"


def test_prompt_builder_duplicate_context_removal() -> None:
    """Verify identical chunk text content is deduplicated in context formatting."""
    chunks = [
        SearchResult(
            document_id="doc-1",
            chunk_id="c-1",
            page_number=5,
            score=0.95,
            text="Duplicate instruction text.",
        ),
        SearchResult(
            document_id="doc-1",
            chunk_id="c-2",
            page_number=6,
            score=0.91,
            text="   Duplicate instruction text.   ",
        ),
    ]

    prompt = PromptBuilder.build_prompt("Duplicate test", chunks, include_page_headers=True)

    # Should only contain one instance of the text block
    assert prompt.context.count("Duplicate instruction text.") == 1
    assert "Page 5" in prompt.context
    assert "Page 6" not in prompt.context


def test_prompt_builder_whitespace_normalization() -> None:
    """Verify whitespace normalization removes redundant blank lines and repeated headers."""
    chunks = [
        SearchResult(
            document_id="doc-1",
            chunk_id="c-1",
            page_number=10,
            score=0.88,
            text="\n\n==========\nPage 10\n\nLine 1\n\n\n\nLine 2\n\n",
        )
    ]

    prompt = PromptBuilder.build_prompt("Whitespace test", chunks, include_page_headers=True)

    assert "Line 1\n\nLine 2" in prompt.context
