"""
Service layer for intelligent, deterministic context selection.
Selects the minimum necessary evidence chunks from pre-filtered search results.
"""

from typing import List, Optional

from backend.core.config import settings
from backend.core.logging import logger
from backend.schemas.evidence import SelectedEvidence
from backend.schemas.search import SearchResult


class ContextSelector:
    """
    Responsible ONLY for selecting the minimum required evidence chunks
    from pre-filtered retrieval results based on deterministic similarity thresholds.

    Must NOT perform:
    - retrieval or embeddings
    - similarity score calculation or threshold alteration
    - vector search reranking
    - confidence evaluation
    - LLM calls or prompt building
    """

    @classmethod
    def select_context(
        cls,
        chunks: List[SearchResult],
        top1_threshold: Optional[float] = None,
        top2_threshold: Optional[float] = None,
        top3_threshold: Optional[float] = None,
    ) -> SelectedEvidence:
        """
        Selects minimum required evidence chunks from filtered chunks while preserving
        ranking order, metadata, chunk text, and similarity scores.

        Args:
            chunks: List of pre-filtered SearchResult chunks (sorted by similarity score descending).
            top1_threshold: Optional override for top 1 selection threshold (default 0.90).
            top2_threshold: Optional override for top 2 selection threshold (default 0.82).
            top3_threshold: Optional override for top 3 selection threshold (default 0.75).

        Returns:
            SelectedEvidence container with selected chunks and selection metadata.
        """
        candidate_count = len(chunks)
        if not chunks:
            logger.info("ContextSelector received 0 candidate chunks. Returning empty SelectedEvidence.")
            return SelectedEvidence(
                chunks=[],
                selected_count=0,
                candidate_count=0,
                highest_score=0.0,
                selection_strategy="empty_candidates",
            )

        t1 = top1_threshold if top1_threshold is not None else settings.EVIDENCE_TOP1_THRESHOLD
        t2 = top2_threshold if top2_threshold is not None else settings.EVIDENCE_TOP2_THRESHOLD
        t3 = top3_threshold if top3_threshold is not None else settings.EVIDENCE_TOP3_THRESHOLD

        highest_score = max(c.score for c in chunks)

        if highest_score >= t1:
            selected_chunks = chunks[:1]
            strategy = "top_1_high_confidence"
        elif highest_score >= t2:
            selected_chunks = chunks[:2]
            strategy = "top_2_medium_confidence"
        elif highest_score >= t3:
            selected_chunks = chunks[:3]
            strategy = "top_3_standard_confidence"
        else:
            selected_chunks = []
            strategy = "empty_below_threshold"

        selected_count = len(selected_chunks)
        logger.info(
            "ContextSelector: candidates=%d, highest_score=%.4f, selected=%d, strategy='%s'",
            candidate_count,
            highest_score,
            selected_count,
            strategy,
        )

        return SelectedEvidence(
            chunks=selected_chunks,
            selected_count=selected_count,
            candidate_count=candidate_count,
            highest_score=highest_score,
            selection_strategy=strategy,
        )
