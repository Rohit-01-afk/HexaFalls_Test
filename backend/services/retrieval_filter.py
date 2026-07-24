"""
Service layer for filtering, deduplicating, sorting, and evaluating RAG retrieval candidates.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from backend.core.config import settings
from backend.core.logging import logger
from backend.schemas.ask import RetrievalDiagnostics
from backend.schemas.search import SearchResult


@dataclass
class FilterResult:
    """
    Structured outcome of the retrieval filtering stage.

    Attributes:
        filtered_chunks: List of SearchResult objects after filtering, sorting, and limits.
        confidence: Deterministic confidence rating ('High', 'Medium', 'Low', 'None').
        diagnostics: Strongly typed RetrievalDiagnostics object.
    """

    filtered_chunks: List[SearchResult] = field(default_factory=list)
    confidence: str = "None"
    diagnostics: Optional[RetrievalDiagnostics] = None


class RetrievalFilter:
    """
    Responsible ONLY for retrieval decision logic:
    - Deduplicating identical chunk IDs
    - Filtering chunks below similarity threshold
    - Sorting chunks descending by similarity score
    - Enforcing Top-K limits
    - Enforcing maximum context character limits (preserving chunk boundaries)
    - Computing deterministic retrieval confidence ratings
    """

    @classmethod
    def filter_chunks(
        cls,
        chunks: List[SearchResult],
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        max_context_chars: Optional[int] = None,
    ) -> FilterResult:
        """
        Applies deduplication, score thresholding, sorting, top-k capping,
        and max character constraints to candidate search chunks.

        Args:
            chunks: Candidate search results from SearchService.
            top_k: Maximum number of top chunks to return. Defaults to settings.RAG_TOP_K.
            similarity_threshold: Minimum cosine similarity score. Defaults to settings.RAG_SIMILARITY_THRESHOLD.
            max_context_chars: Cumulative character cap for context text. Defaults to settings.RAG_MAX_CONTEXT_CHARS.

        Returns:
            FilterResult object containing filtered SearchResult list, confidence, and diagnostics.
        """
        target_top_k = top_k if top_k is not None else settings.RAG_TOP_K
        target_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else settings.RAG_SIMILARITY_THRESHOLD
        )
        target_max_chars = (
            max_context_chars
            if max_context_chars is not None
            else settings.RAG_MAX_CONTEXT_CHARS
        )

        raw_count = len(chunks)
        if raw_count == 0:
            logger.info("RetrievalFilter received 0 chunks. Returning empty FilterResult.")
            empty_diag = RetrievalDiagnostics(
                raw_count=0,
                deduplicated_count=0,
                filtered_count=0,
                returned_count=0,
                confidence="None",
                filter_reason="empty_search_results",
                similarity_threshold=target_threshold,
                top_k=target_top_k,
                max_context_chars=target_max_chars,
            )
            return FilterResult(
                filtered_chunks=[],
                confidence="None",
                diagnostics=empty_diag,
            )

        # 1. Deduplicate by chunk_id, preserving chunk with highest score
        dedup_map: Dict[str, SearchResult] = {}
        for chunk in chunks:
            cid = chunk.chunk_id
            if cid not in dedup_map or chunk.score > dedup_map[cid].score:
                dedup_map[cid] = chunk

        deduped_list = list(dedup_map.values())
        deduped_count = len(deduped_list)

        # 2. Sort descending by similarity score
        sorted_list = sorted(deduped_list, key=lambda c: c.score, reverse=True)

        # 3. Filter out chunks below similarity threshold
        above_threshold = [c for c in sorted_list if c.score >= target_threshold]
        filtered_count = len(above_threshold)

        reason: Optional[str] = None
        if filtered_count == 0:
            reason = "filtered_below_threshold"
            logger.info(
                "RetrievalFilter filtered all %d chunks below similarity threshold %.2f",
                deduped_count,
                target_threshold,
            )

        # 4. Limit to top_k
        top_k_list = above_threshold[:target_top_k]

        # 5. Limit by max_context_chars cumulative length without breaking chunk boundaries
        final_chunks: List[SearchResult] = []
        accumulated_chars = 0
        for chunk in top_k_list:
            chunk_len = len(chunk.text)
            if accumulated_chars + chunk_len > target_max_chars and final_chunks:
                # Max context length reached, preserve chunk boundary and stop
                reason = reason or "max_context_chars_reached"
                break
            final_chunks.append(chunk)
            accumulated_chars += chunk_len

        returned_count = len(final_chunks)

        # 6. Compute deterministic confidence rating based on similarity scores
        confidence = cls._compute_confidence(final_chunks)

        diagnostics = RetrievalDiagnostics(
            raw_count=raw_count,
            deduplicated_count=deduped_count,
            filtered_count=filtered_count,
            returned_count=returned_count,
            confidence=confidence,
            filter_reason=reason,
            similarity_threshold=target_threshold,
            top_k=target_top_k,
            max_context_chars=target_max_chars,
        )

        logger.info(
            "RetrievalFilter complete: %d -> %d -> %d -> %d chunks (confidence=%s, reason=%s)",
            raw_count,
            deduped_count,
            filtered_count,
            returned_count,
            confidence,
            reason,
        )

        return FilterResult(
            filtered_chunks=final_chunks,
            confidence=confidence,
            diagnostics=diagnostics,
        )

    @classmethod
    def _compute_confidence(cls, chunks: List[SearchResult]) -> str:
        """
        Computes deterministic retrieval confidence level from retained similarity scores.

        Rules:
            - If no chunks returned: "None"
            - Max score >= 0.85 and average score >= 0.80: "High"
            - Max score >= 0.75: "Medium"
            - Otherwise: "Low"
        """
        if not chunks:
            return "None"

        top_score = max(c.score for c in chunks)
        avg_score = sum(c.score for c in chunks) / len(chunks)

        if top_score >= 0.85 and avg_score >= 0.80:
            return "High"
        elif top_score >= 0.75:
            return "Medium"
        else:
            return "Low"
