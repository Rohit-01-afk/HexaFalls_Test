"""
Data models for structured context and evidence selection.
"""

from dataclasses import dataclass, field
from typing import List

from backend.schemas.search import SearchResult


@dataclass(frozen=True)
class SelectedEvidence:
    """
    Immutable dataclass representing selected evidence chunks and selection diagnostics.

    Attributes:
        chunks: List of SearchResult chunks selected for prompt context.
        selected_count: Number of chunks selected.
        candidate_count: Number of candidate chunks received from retrieval filter.
        highest_score: Highest similarity score among candidate chunks.
        selection_strategy: Identifier string for selection strategy applied.
    """

    chunks: List[SearchResult] = field(default_factory=list)
    selected_count: int = 0
    candidate_count: int = 0
    highest_score: float = 0.0
    selection_strategy: str = "none"
