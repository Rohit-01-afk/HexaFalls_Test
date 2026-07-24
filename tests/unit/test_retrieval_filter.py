"""
Unit tests for RetrievalFilter service: deduplication, threshold filtering, score sorting,
Top-K limiting, max context character capping, and confidence evaluation.
"""

import pytest

from backend.core.config import settings
from backend.schemas.search import SearchResult
from backend.services.retrieval_filter import FilterResult, RetrievalFilter


def test_retrieval_filter_empty_input() -> None:
    """Verify empty candidate list returns empty FilterResult with 'None' confidence."""
    res = RetrievalFilter.filter_chunks([])
    assert res.filtered_chunks == []
    assert res.confidence == "None"
    assert res.diagnostics is not None
    assert res.diagnostics.raw_count == 0
    assert res.diagnostics.returned_count == 0
    assert res.diagnostics.filter_reason == "empty_search_results"


def test_retrieval_filter_deduplication() -> None:
    """Verify duplicate chunk IDs are deduplicated, keeping the highest similarity score."""
    chunks = [
        SearchResult(
            document_id="doc-1",
            chunk_id="chunk-dup",
            page_number=1,
            score=0.70,
            text="Lower score duplicate text.",
        ),
        SearchResult(
            document_id="doc-1",
            chunk_id="chunk-dup",
            page_number=1,
            score=0.90,
            text="Higher score duplicate text.",
        ),
        SearchResult(
            document_id="doc-1",
            chunk_id="chunk-unique",
            page_number=2,
            score=0.82,
            text="Unique chunk text.",
        ),
    ]

    res = RetrievalFilter.filter_chunks(chunks, similarity_threshold=0.70)

    assert len(res.filtered_chunks) == 2
    assert res.diagnostics is not None
    assert res.diagnostics.raw_count == 3
    assert res.diagnostics.deduplicated_count == 2
    dup_chunk = next(c for c in res.filtered_chunks if c.chunk_id == "chunk-dup")
    assert dup_chunk.score == 0.90
    assert dup_chunk.text == "Higher score duplicate text."


def test_retrieval_filter_sorting_and_thresholding() -> None:
    """Verify chunks are sorted descending by score and those below threshold are removed."""
    chunks = [
        SearchResult(document_id="d1", chunk_id="c1", page_number=1, score=0.60, text="Text 1"),
        SearchResult(document_id="d1", chunk_id="c2", page_number=2, score=0.88, text="Text 2"),
        SearchResult(document_id="d1", chunk_id="c3", page_number=3, score=0.76, text="Text 3"),
        SearchResult(document_id="d1", chunk_id="c4", page_number=4, score=0.72, text="Text 4"),
    ]

    res = RetrievalFilter.filter_chunks(chunks, similarity_threshold=0.75)

    assert len(res.filtered_chunks) == 2
    assert res.filtered_chunks[0].chunk_id == "c2"
    assert res.filtered_chunks[0].score == 0.88
    assert res.filtered_chunks[1].chunk_id == "c3"
    assert res.filtered_chunks[1].score == 0.76


def test_retrieval_filter_all_below_threshold() -> None:
    """Verify filter_reason='filtered_below_threshold' when all candidate chunks are below threshold."""
    chunks = [
        SearchResult(document_id="d1", chunk_id="c1", page_number=1, score=0.50, text="Text 1"),
        SearchResult(document_id="d1", chunk_id="c2", page_number=2, score=0.65, text="Text 2"),
    ]

    res = RetrievalFilter.filter_chunks(chunks, similarity_threshold=0.75)

    assert res.filtered_chunks == []
    assert res.confidence == "None"
    assert res.diagnostics is not None
    assert res.diagnostics.filter_reason == "filtered_below_threshold"
    assert res.diagnostics.filtered_count == 0


def test_retrieval_filter_top_k_limiting() -> None:
    """Verify results are capped to top_k limit."""
    chunks = [
        SearchResult(document_id="d1", chunk_id=f"c{i}", page_number=i, score=0.90 - (i * 0.01), text=f"Chunk {i}")
        for i in range(10)
    ]

    res = RetrievalFilter.filter_chunks(chunks, top_k=3, similarity_threshold=0.70)

    assert len(res.filtered_chunks) == 3
    assert res.filtered_chunks[0].chunk_id == "c0"
    assert res.filtered_chunks[2].chunk_id == "c2"


def test_retrieval_filter_max_context_chars_limiting() -> None:
    """Verify chunks are included up to max_context_chars cap without splitting chunks."""
    chunk1_text = "A" * 100
    chunk2_text = "B" * 100
    chunk3_text = "C" * 100

    chunks = [
        SearchResult(document_id="d1", chunk_id="c1", page_number=1, score=0.95, text=chunk1_text),
        SearchResult(document_id="d1", chunk_id="c2", page_number=2, score=0.90, text=chunk2_text),
        SearchResult(document_id="d1", chunk_id="c3", page_number=3, score=0.85, text=chunk3_text),
    ]

    # Limit max context chars to 250 (fits chunk1 + chunk2, but not chunk3)
    res = RetrievalFilter.filter_chunks(chunks, max_context_chars=250, similarity_threshold=0.70)

    assert len(res.filtered_chunks) == 2
    assert [c.chunk_id for c in res.filtered_chunks] == ["c1", "c2"]
    assert res.diagnostics is not None
    assert res.diagnostics.filter_reason == "max_context_chars_reached"


def test_retrieval_filter_confidence_levels() -> None:
    """Verify deterministic confidence calculation for High, Medium, Low ratings."""
    high_chunks = [
        SearchResult(document_id="d1", chunk_id="c1", page_number=1, score=0.88, text="Text 1"),
        SearchResult(document_id="d1", chunk_id="c2", page_number=2, score=0.82, text="Text 2"),
    ]
    med_chunks = [
        SearchResult(document_id="d1", chunk_id="c1", page_number=1, score=0.78, text="Text 1"),
    ]
    low_chunks = [
        SearchResult(document_id="d1", chunk_id="c1", page_number=1, score=0.60, text="Text 1"),
    ]

    res_high = RetrievalFilter.filter_chunks(high_chunks, similarity_threshold=0.50)
    assert res_high.confidence == "High"

    res_med = RetrievalFilter.filter_chunks(med_chunks, similarity_threshold=0.50)
    assert res_med.confidence == "Medium"

    res_low = RetrievalFilter.filter_chunks(low_chunks, similarity_threshold=0.50)
    assert res_low.confidence == "Low"
