"""
Unit tests for ContextSelector deterministic adaptive context selection strategy.
"""

import pytest
from backend.schemas.evidence import SelectedEvidence
from backend.schemas.search import SearchResult
from backend.services.context_selector import ContextSelector


def test_context_selector_empty_input() -> None:
    """Verify empty input returns empty SelectedEvidence with candidate_count=0."""
    result = ContextSelector.select_context([])
    assert isinstance(result, SelectedEvidence)
    assert result.selected_count == 0
    assert result.candidate_count == 0
    assert result.highest_score == 0.0
    assert result.selection_strategy == "empty_candidates"
    assert result.chunks == []


def test_context_selector_top_1_high_confidence() -> None:
    """Verify highest similarity >= 0.90 selects Top 1 chunk."""
    chunks = [
        SearchResult(document_id="d1", chunk_id="c1", page_number=1, score=0.95, text="Chunk 1"),
        SearchResult(document_id="d1", chunk_id="c2", page_number=2, score=0.88, text="Chunk 2"),
        SearchResult(document_id="d1", chunk_id="c3", page_number=3, score=0.80, text="Chunk 3"),
    ]
    result = ContextSelector.select_context(chunks)
    assert result.selected_count == 1
    assert result.candidate_count == 3
    assert result.highest_score == 0.95
    assert result.selection_strategy == "top_1_high_confidence"
    assert len(result.chunks) == 1
    assert result.chunks[0].chunk_id == "c1"


def test_context_selector_top_2_medium_confidence() -> None:
    """Verify highest similarity >= 0.82 and < 0.90 selects Top 2 chunks."""
    chunks = [
        SearchResult(document_id="d1", chunk_id="c1", page_number=1, score=0.86, text="Chunk 1"),
        SearchResult(document_id="d1", chunk_id="c2", page_number=2, score=0.83, text="Chunk 2"),
        SearchResult(document_id="d1", chunk_id="c3", page_number=3, score=0.79, text="Chunk 3"),
    ]
    result = ContextSelector.select_context(chunks)
    assert result.selected_count == 2
    assert result.candidate_count == 3
    assert result.highest_score == 0.86
    assert result.selection_strategy == "top_2_medium_confidence"
    assert len(result.chunks) == 2
    assert [c.chunk_id for c in result.chunks] == ["c1", "c2"]


def test_context_selector_top_3_standard_confidence() -> None:
    """Verify highest similarity >= 0.75 and < 0.82 selects Top 3 chunks."""
    chunks = [
        SearchResult(document_id="d1", chunk_id="c1", page_number=1, score=0.78, text="Chunk 1"),
        SearchResult(document_id="d1", chunk_id="c2", page_number=2, score=0.77, text="Chunk 2"),
        SearchResult(document_id="d1", chunk_id="c3", page_number=3, score=0.76, text="Chunk 3"),
        SearchResult(document_id="d1", chunk_id="c4", page_number=4, score=0.75, text="Chunk 4"),
    ]
    result = ContextSelector.select_context(chunks)
    assert result.selected_count == 3
    assert result.candidate_count == 4
    assert result.highest_score == 0.78
    assert result.selection_strategy == "top_3_standard_confidence"
    assert len(result.chunks) == 3
    assert [c.chunk_id for c in result.chunks] == ["c1", "c2", "c3"]


def test_context_selector_empty_below_threshold() -> None:
    """Verify highest similarity < 0.75 returns empty selection strategy."""
    chunks = [
        SearchResult(document_id="d1", chunk_id="c1", page_number=1, score=0.72, text="Chunk 1"),
        SearchResult(document_id="d1", chunk_id="c2", page_number=2, score=0.68, text="Chunk 2"),
    ]
    result = ContextSelector.select_context(chunks)
    assert result.selected_count == 0
    assert result.candidate_count == 2
    assert result.highest_score == 0.72
    assert result.selection_strategy == "empty_below_threshold"
    assert result.chunks == []


def test_context_selector_immutability() -> None:
    """Verify SelectedEvidence is an immutable frozen dataclass."""
    result = SelectedEvidence(chunks=[], selected_count=0, candidate_count=0, highest_score=0.0, selection_strategy="none")
    with pytest.raises(Exception):
        result.selected_count = 5  # type: ignore[misc]


def test_context_selector_preserves_metadata_and_ordering() -> None:
    """Verify ranking order, scores, page numbers, and chunk texts are preserved untouched."""
    chunks = [
        SearchResult(document_id="doc-abc", chunk_id="chk-001", page_number=12, score=0.92, text="Original text 1"),
        SearchResult(document_id="doc-abc", chunk_id="chk-002", page_number=13, score=0.88, text="Original text 2"),
    ]
    result = ContextSelector.select_context(chunks)
    selected_chunk = result.chunks[0]
    assert selected_chunk.document_id == "doc-abc"
    assert selected_chunk.chunk_id == "chk-001"
    assert selected_chunk.page_number == 12
    assert selected_chunk.score == 0.92
    assert selected_chunk.text == "Original text 1"
