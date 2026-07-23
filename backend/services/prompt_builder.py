"""
Service layer for constructing grounded system prompts and context structures.
"""

from dataclasses import dataclass
from typing import List
from backend.schemas.search import SearchResult

SYSTEM_PROMPT = (
    "You are Blueprint Eye,\n"
    "an AI assistant specialized in technical manuals.\n\n"
    "Answer ONLY using the supplied context.\n\n"
    "Never invent information.\n\n"
    "Never use outside knowledge.\n\n"
    "If the answer cannot be found in the supplied context,\n"
    'reply exactly:\n\n"I could not find this information in the manual."\n\n'
    "Preserve technical terminology whenever possible.\n\n"
    "Keep answers concise and accurate."
)


@dataclass(frozen=True)
class Prompt:
    """
    Immutable representation of a constructed RAG prompt.

    Attributes:
        system: System instructions and grounding rules for the AI model.
        context: Extracted text context formatted with page numbers.
        user: The original user question.
    """

    system: str
    context: str
    user: str


class PromptBuilder:
    """Responsible ONLY for constructing immutable Prompt objects."""

    @classmethod
    def build_prompt(cls, question: str, chunks: List[SearchResult]) -> Prompt:
        """
        Constructs an immutable Prompt object containing grounded system instructions,
        formatted chunk context with page numbers, and user question.

        Args:
            question: The user's natural language question.
            chunks: List of top-k retrieved SearchResult chunks.

        Returns:
            Immutable Prompt dataclass instance.
        """
        context_blocks: List[str] = []

        for chunk in chunks:
            block = f"[Page {chunk.page_number}]\n{chunk.text.strip()}"
            context_blocks.append(block)

        formatted_context = "\n\n".join(context_blocks)

        return Prompt(
            system=SYSTEM_PROMPT,
            context=formatted_context,
            user=question.strip(),
        )
