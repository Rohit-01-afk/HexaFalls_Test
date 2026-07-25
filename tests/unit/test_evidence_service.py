"""
Unit tests for EvidencePreparer, EvidenceBlock data model, and PreparedEvidence container.
"""

from backend.schemas.search import SearchResult
from backend.services.evidence_service import EvidenceBlock, EvidencePreparer, PreparedEvidence


def test_evidence_block_model() -> None:
    """Verify EvidenceBlock is an immutable dataclass storing structured metadata."""
    block = EvidenceBlock(
        content="Sample text content",
        page_number=14,
        score=0.88,
        retrieval_order=1,
        evidence_type="text",
        category="primary",
    )
    assert block.content == "Sample text content"
    assert block.page_number == 14
    assert block.score == 0.88
    assert block.retrieval_order == 1
    assert block.evidence_type == "text"
    assert block.category == "primary"


def test_evidence_preparer_empty_chunks() -> None:
    """Verify EvidencePreparer handles empty chunk list cleanly."""
    evidence = EvidencePreparer.prepare_evidence([])
    assert isinstance(evidence, PreparedEvidence)
    assert len(evidence.blocks) == 0
    assert evidence.primary_count == 0
    assert evidence.supporting_count == 0


def test_evidence_preparer_classification_and_order() -> None:
    """Verify EvidencePreparer cleans text, preserves order, and assigns primary/supporting categories."""
    chunks = [
        SearchResult(
            document_id="doc1",
            chunk_id="c1",
            page_number=10,
            score=0.92,
            text="Primary step 1 instruction.",
        ),
        SearchResult(
            document_id="doc1",
            chunk_id="c2",
            page_number=11,
            score=0.90,
            text="Primary step 2 instruction (close score delta).",
        ),
        SearchResult(
            document_id="doc1",
            chunk_id="c3",
            page_number=12,
            score=0.70,
            text="Supporting background reference text.",
        ),
    ]

    evidence = EvidencePreparer.prepare_evidence(chunks)

    assert len(evidence.blocks) == 3
    assert evidence.primary_count == 2
    assert evidence.supporting_count == 1

    # Verify order preservation
    assert evidence.blocks[0].retrieval_order == 1
    assert evidence.blocks[0].page_number == 10
    assert evidence.blocks[0].category == "primary"

    assert evidence.blocks[1].retrieval_order == 2
    assert evidence.blocks[1].category == "primary"

    assert evidence.blocks[2].retrieval_order == 3
    assert evidence.blocks[2].category == "supporting"
