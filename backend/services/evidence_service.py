"""
Service layer for evidence preparation and classification.
EvidencePreparer formats structured evidence blocks without generating prompt text.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from backend.core.config import settings
from backend.core.logging import logger, write_debug_file
from backend.schemas.search import SearchResult


@dataclass(frozen=True)
class EvidenceBlock:
    """
    Immutable representation of an individual structured evidence block.

    Attributes:
        content: Cleaned text content of the retrieved chunk.
        page_number: Source manual page number.
        score: Semantic similarity score.
        retrieval_order: Original 1-indexed retrieval rank order.
        evidence_type: Type of evidence (default 'text').
        category: Evidence rank category ('primary' vs 'supporting').
    """

    content: str
    page_number: int
    score: float
    retrieval_order: int
    evidence_type: str = "text"
    category: str = "primary"


@dataclass(frozen=True)
class PreparedEvidence:
    """
    Structured collection of evidence blocks prepared for prompt construction.

    Attributes:
        blocks: List of EvidenceBlock instances.
        primary_count: Dynamic count of primary evidence blocks.
        supporting_count: Dynamic count of supporting evidence blocks.
    """

    blocks: List[EvidenceBlock] = field(default_factory=list)

    @property
    def primary_count(self) -> int:
        return sum(1 for b in self.blocks if b.category == "primary")

    @property
    def supporting_count(self) -> int:
        return sum(1 for b in self.blocks if b.category == "supporting")


class EvidencePreparer:
    """
    Responsible ONLY for preparing structured evidence blocks from retrieved SearchResult chunks.
    Must NEVER generate prompt text or perform LLM calls.
    """

    @classmethod
    def prepare_evidence(
        cls,
        chunks: List[SearchResult],
        generation_id: Optional[str] = None,
    ) -> PreparedEvidence:
        """
        Cleans whitespace, preserves retrieval order and similarity scores,
        and assigns rank-based evidence categories without discarding any chunks.

        Args:
            chunks: List of pre-filtered SearchResult chunks.
            generation_id: Optional unique generation identifier for tracing.

        Returns:
            PreparedEvidence dataclass container.
        """
        gen_id = generation_id or "gen-unknown"


        if not chunks:
            evidence = PreparedEvidence(blocks=[])
            if getattr(settings, "DEBUG_RAG_PIPELINE", False):
                empty_log = (
                    f"===== EVIDENCE SUMMARY =====\n\n"
                    f"Generation ID: {gen_id}\n"
                    f"Primary evidence count: 0\n"
                    f"Supporting evidence count: 0\n"
                    f"Total evidence blocks: 0\n"
                    f"Total context characters: 0\n"
                    f"Page numbers used: []\n\n"
                    f"===== PREPARED EVIDENCE =====\n\n"
                    f"Generation ID: {gen_id}\n\n"
                    f"[No evidence prepared]\n"
                )
                logger.info("\n%s", empty_log)
                write_debug_file("prepared_evidence.txt", empty_log)
            return evidence

        blocks: List[EvidenceBlock] = []
        top_score = max(c.score for c in chunks) if chunks else 0.0

        for idx, chunk in enumerate(chunks, start=1):
            cleaned_text = cls._normalize_whitespace(chunk.text)
            if not cleaned_text:
                continue

            category = "primary" if (idx == 1 or chunk.score >= top_score - 0.05) else "supporting"

            block = EvidenceBlock(
                content=cleaned_text,
                page_number=chunk.page_number,
                score=chunk.score,
                retrieval_order=idx,
                evidence_type="text",
                category=category,
            )
            blocks.append(block)

        evidence = PreparedEvidence(blocks=blocks)

        if getattr(settings, "DEBUG_RAG_PIPELINE", False):
            total_chars = sum(len(b.content) for b in evidence.blocks)
            page_numbers = sorted(list(set(b.page_number for b in evidence.blocks)))
            formatted_blocks = [
                f"[Page {b.page_number} | {b.category.upper()} | Score: {b.score:.2f}]\n{b.content}"
                for b in evidence.blocks
            ]
            formatted_text = "\n\n".join(formatted_blocks)

            evidence_log_content = (
                f"===== EVIDENCE SUMMARY =====\n\n"
                f"Generation ID: {gen_id}\n"
                f"Primary evidence count: {evidence.primary_count}\n"
                f"Supporting evidence count: {evidence.supporting_count}\n"
                f"Total evidence blocks: {len(evidence.blocks)}\n"
                f"Total context characters: {total_chars}\n"
                f"Page numbers used: {page_numbers}\n\n"
                f"===== PREPARED EVIDENCE =====\n\n"
                f"Generation ID: {gen_id}\n\n"
                f"{formatted_text if formatted_text else '[Empty evidence text]'}\n"
            )
            write_debug_file("prepared_evidence.txt", evidence_log_content)

        return evidence

    @classmethod
    def _normalize_whitespace(cls, text: str) -> str:
        """Removes excessive blank lines and normalizes whitespace."""
        if not text:
            return ""
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        normalized = re.sub(r"^(?:==========|Page \d+)\n", "", normalized, flags=re.MULTILINE)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        return normalized.strip()
