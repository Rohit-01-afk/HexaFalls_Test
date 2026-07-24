"""
Service layer for constructing grounded system prompts and context structures.
PromptBuilder is a pure formatting component. It receives pre-filtered chunks
and formats immutable Prompt objects without making any retrieval, ranking, or threshold decisions.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Set

from backend.core.config import settings
from backend.schemas.search import SearchResult

SYSTEM_PROMPT = (
    "You are Blueprint Eye, an AI assistant specialized in technical manuals.\n\n"
    "SYSTEM INSTRUCTIONS & GROUNDING RULES:\n"
    "1. Answer ONLY using the supplied manual context. Never use outside knowledge or fabricate information.\n"
    "2. Be deterministic and direct. Do NOT reveal internal reasoning, chain-of-thought, or step-by-step thinking.\n"
    "3. Support Distinction:\n"
    "   - Fully supported information: Provide precise, complete technical answers.\n"
    "   - Partially supported information: State the available facts clearly without speculation.\n"
    "   - Unsupported information: If the answer cannot be found in the context, reply exactly: "
    '"I could not find this information in the manual."\n'
    "4. Preserve technical terminology, model numbers, signal names, and pin/cable designations exactly as written.\n"
    "5. Format responses clearly with concise technical explanations. Prefer structured layout (Answer, Additional Details if appropriate, and Sources)."
)


@dataclass(frozen=True)
class Prompt:
    """
    Immutable representation of a constructed RAG prompt.

    Attributes:
        system: System instructions and grounding rules for the AI model.
        context: Extracted text context formatted with page numbers and metadata.
        user: The original user question.
    """

    system: str
    context: str
    user: str


class PromptBuilder:
    """
    Responsible ONLY for pure context formatting and immutable Prompt construction.
    Must NEVER perform retrieval, chunk ranking, similarity score calculation,
    confidence evaluation, threshold filtering, or fallback decision-making.
    """

    @classmethod
    def build_prompt(
        cls,
        question: str,
        chunks: List[SearchResult],
        include_page_headers: Optional[bool] = None,
    ) -> Prompt:
        """
        Constructs an immutable Prompt object containing grounded system instructions,
        cleaned and formatted context blocks with page numbers, and the user question.

        Args:
            question: The user's natural language question.
            chunks: List of pre-filtered SearchResult chunks.
            include_page_headers: Optional override for header formatting. Defaults to settings.RAG_INCLUDE_PAGE_HEADERS.

        Returns:
            Immutable Prompt dataclass instance.
        """
        use_headers = (
            include_page_headers
            if include_page_headers is not None
            else settings.RAG_INCLUDE_PAGE_HEADERS
        )

        formatted_context = cls._format_context(chunks, use_headers=use_headers)

        return Prompt(
            system=SYSTEM_PROMPT,
            context=formatted_context,
            user=question.strip(),
        )

    @classmethod
    def _format_context(cls, chunks: List[SearchResult], use_headers: bool) -> str:
        """
        Cleans, normalizes, deduplicates, and formats context blocks from filtered chunks.
        """
        if not chunks:
            return ""

        context_blocks: List[str] = []
        seen_texts: Set[str] = set()

        for chunk in chunks:
            cleaned_text = cls._normalize_whitespace(chunk.text)
            if not cleaned_text:
                continue

            # Deduplicate identical chunk content
            dedup_key = cleaned_text.lower()
            if dedup_key in seen_texts:
                continue
            seen_texts.add(dedup_key)

            if use_headers:
                block = (
                    f"==========\n"
                    f"Page {chunk.page_number}\n"
                    f"Similarity: {chunk.score:.2f}\n"
                    f"Content:\n"
                    f"{cleaned_text}"
                )
            else:
                block = f"[Page {chunk.page_number}]\n{cleaned_text}"

            context_blocks.append(block)

        return "\n\n".join(context_blocks)

    @classmethod
    def _normalize_whitespace(cls, text: str) -> str:
        """
        Removes excessive blank lines, repeated headers, and normalizes space boundaries.
        """
        if not text:
            return ""

        # Normalize line endings
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")

        # Strip redundant repeated header lines (e.g. repeated "==========\n" or "Page X\n")
        normalized = re.sub(r"^(?:==========|Page \d+)\n", "", normalized, flags=re.MULTILINE)

        # Collapse 3 or more newlines to 2 newlines (preserve paragraph boundaries)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)

        return normalized.strip()

