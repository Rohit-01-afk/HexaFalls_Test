"""
Service layer for constructing grounded system prompts and context structures.
PromptBuilder is a pure formatting component. It receives pre-filtered chunks
or prepared evidence and formats immutable Prompt objects without making retrieval decisions.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Set, Union

from backend.core.config import settings
from backend.core.logging import logger, write_debug_file
from backend.schemas.evidence import SelectedEvidence
from backend.schemas.query_intent import QueryIntent, QueryIntentType
from backend.schemas.search import SearchResult
from backend.services.evidence_service import EvidenceBlock, EvidencePreparer, PreparedEvidence

PROMPT_VERSION = "2.1"

SYSTEM_PROMPT = (
    "You are Blueprint Eye.\n\n"
    "You are an enterprise document extraction assistant.\n\n"
    "Use ONLY the provided document context.\n\n"
    "Do not use outside knowledge.\n\n"
    "Do not continue the document.\n\n"
    "Do not invent procedures.\n\n"
    "Do not summarize unrelated content.\n\n"
    "Answer only from the supplied evidence.\n\n"
    "If the answer is unavailable, reply exactly:\n\n"
    "'I could not find this information in the manual.'"
)

RECOVERY_SYSTEM_PROMPT = SYSTEM_PROMPT


@dataclass(frozen=True)
class Prompt:
    """
    Immutable representation of structured RAG prompt data.
    Contains only data attributes required to render prompts.

    Attributes:
        system: System instructions and grounding rules for the AI model.
        context: Extracted text context formatted with page numbers and metadata.
        user: The original user question.
        intent: Optional detected query intent type.
        is_recovery: True if this prompt is a lightweight recovery prompt.
        generation_id: Optional unique generation identifier for tracing.
    """

    system: str
    context: str
    user: str
    intent: Optional[QueryIntentType] = None
    is_recovery: bool = False
    generation_id: Optional[str] = None


class PromptBuilder:
    """
    Responsible ONLY for pure context formatting, prompt model construction,
    and rendering structured prompt strings (both standard and recovery prompts).
    Must NEVER perform retrieval, chunk ranking, similarity score calculation,
    confidence evaluation, threshold filtering, response validation, or recovery execution.
    """

    PROMPT_VERSION: str = PROMPT_VERSION

    @classmethod
    def build_prompt(
        cls,
        question: str,
        chunks_or_evidence: Union[SelectedEvidence, PreparedEvidence, List[SearchResult]],
        intent: Optional[QueryIntent] = None,
        include_page_headers: Optional[bool] = None,
        generation_id: Optional[str] = None,
    ) -> Prompt:
        """
        Constructs an immutable standard Prompt object containing grounded system instructions,
        formatted evidence blocks, user question, and optional intent classification.

        Args:
            question: The user's natural language question.
            chunks_or_evidence: SelectedEvidence model, PreparedEvidence container, or List of SearchResult chunks.
            intent: Optional QueryIntent classification metadata from QueryUnderstandingService.
            include_page_headers: Optional override for header formatting.
            generation_id: Optional unique generation identifier for tracing.

        Returns:
            Immutable Prompt dataclass instance.
        """
        gen_id = generation_id or "gen-unknown"
        use_headers = (
            include_page_headers
            if include_page_headers is not None
            else settings.RAG_INCLUDE_PAGE_HEADERS
        )

        if isinstance(chunks_or_evidence, SelectedEvidence):
            evidence = EvidencePreparer.prepare_evidence(chunks_or_evidence.chunks, generation_id=gen_id)
        elif isinstance(chunks_or_evidence, PreparedEvidence):
            evidence = chunks_or_evidence
        else:
            evidence = EvidencePreparer.prepare_evidence(chunks_or_evidence, generation_id=gen_id)

        formatted_context = cls._format_evidence_context(evidence, use_headers=use_headers)
        intent_type = intent.intent if intent is not None else None

        prompt = Prompt(
            system=SYSTEM_PROMPT,
            context=formatted_context,
            user=question.strip(),
            intent=intent_type,
            is_recovery=False,
            generation_id=gen_id,
        )

        if getattr(settings, "DEBUG_RAG_PIPELINE", False):
            logger.info(
                "\n===== PROMPT MODEL =====\n\nGeneration ID: %s\nSystem prompt length: %d\nContext length: %d\nQuestion: %s\nRecovery flag: %s\n\nComplete context text:\n%s\n",
                gen_id,
                len(prompt.system),
                len(prompt.context),
                prompt.user,
                prompt.is_recovery,
                prompt.context if prompt.context else "[No context provided]",
            )

        return prompt

    @classmethod
    def build_recovery_prompt(
        cls,
        question: str,
        chunks_or_evidence: Union[SelectedEvidence, PreparedEvidence, List[SearchResult]],
        intent: Optional[QueryIntent] = None,
        include_page_headers: Optional[bool] = None,
        generation_id: Optional[str] = None,
    ) -> Prompt:
        """
        Constructs a concise, extraction-oriented lightweight Prompt object for recovery retries.

        Args:
            question: The user's natural language question.
            chunks_or_evidence: SelectedEvidence model, PreparedEvidence container, or List of SearchResult chunks.
            intent: Optional QueryIntent classification metadata.
            include_page_headers: Optional override for header formatting.
            generation_id: Optional unique generation identifier for tracing.

        Returns:
            Immutable Prompt dataclass instance with is_recovery=True.
        """
        gen_id = generation_id or "gen-unknown"
        use_headers = (
            include_page_headers
            if include_page_headers is not None
            else settings.RAG_INCLUDE_PAGE_HEADERS
        )

        if isinstance(chunks_or_evidence, SelectedEvidence):
            evidence = EvidencePreparer.prepare_evidence(chunks_or_evidence.chunks, generation_id=gen_id)
        elif isinstance(chunks_or_evidence, PreparedEvidence):
            evidence = chunks_or_evidence
        else:
            evidence = EvidencePreparer.prepare_evidence(chunks_or_evidence, generation_id=gen_id)

        formatted_context = cls._format_evidence_context(evidence, use_headers=use_headers)
        intent_type = intent.intent if intent is not None else None

        prompt = Prompt(
            system=RECOVERY_SYSTEM_PROMPT,
            context=formatted_context,
            user=question.strip(),
            intent=intent_type,
            is_recovery=True,
            generation_id=gen_id,
        )

        if getattr(settings, "DEBUG_RAG_PIPELINE", False):
            logger.info(
                "\n===== PROMPT MODEL =====\n\nGeneration ID: %s\nSystem prompt length: %d\nContext length: %d\nQuestion: %s\nRecovery flag: %s\n\nComplete context text:\n%s\n",
                gen_id,
                len(prompt.system),
                len(prompt.context),
                prompt.user,
                prompt.is_recovery,
                prompt.context if prompt.context else "[No context provided]",
            )

        return prompt

    @classmethod
    def render_prompt(cls, prompt: Prompt, generation_id: Optional[str] = None) -> str:
        """
        Renders the final structured prompt string from a Prompt data model.
        Formats sections into DOCUMENT context, QUESTION, and ANSWER marker.

        Args:
            prompt: Prompt dataclass instance.
            generation_id: Optional override unique generation identifier for tracing.

        Returns:
            Formatted user prompt string ready for LLM consumption.
        """
        gen_id = generation_id or prompt.generation_id or "gen-unknown"
        context_text = prompt.context if prompt.context else "[No context provided]"

        rendered = (
            "====================\n\n"
            "DOCUMENT\n\n"
            f"{context_text}\n\n"
            "QUESTION\n\n"
            f"{prompt.user}\n\n"
            "ANSWER"
        )

        if getattr(settings, "DEBUG_RAG_PIPELINE", False):
            rendered_debug_content = (
                f"===== FINAL RENDERED PROMPT =====\n\n"
                f"Generation ID: {gen_id}\n\n"
                f"{rendered}\n"
            )
            write_debug_file("rendered_prompt.txt", rendered_debug_content)

        return rendered

    @classmethod
    def count_context_blocks(cls, context: str) -> int:
        """
        Dynamically computes the number of context blocks in a formatted context string.
        Derived helper to avoid storing redundant state in Prompt model.
        """
        if not context or not context.strip():
            return 0

        blocks = [b.strip() for b in context.strip().split("\n\n") if b.strip()]
        return len(blocks)

    @classmethod
    def _get_intent_instruction(cls, intent: Optional[QueryIntentType]) -> str:
        """Returns tailored instruction line based on detected query intent."""
        if intent == QueryIntentType.PROCEDURE:
            return "4. Format your response as clear, numbered step-by-step instructions in sequential order."
        if intent == QueryIntentType.DEFINITION:
            return "4. Provide a concise, direct definition first, followed by supporting technical details."
        if intent == QueryIntentType.COMPARISON:
            return "4. Organize the response into a structured comparison (e.g., table or bullet points) contrasting key features."
        if intent == QueryIntentType.SAFETY:
            return "4. Prioritize and clearly highlight all safety warnings, precautions, and protective measures."
        if intent == QueryIntentType.DIAGRAM:
            return "4. Reference specific diagram labels, signal names, pin connections, or visual components where applicable."
        if intent == QueryIntentType.TROUBLESHOOTING:
            return "4. Present a structured diagnostic breakdown covering symptoms, root causes, and corrective actions."
        return "4. Provide a clear, direct, and structured technical response."

    @classmethod
    def _format_evidence_context(cls, evidence: PreparedEvidence, use_headers: bool) -> str:
        """Cleans and formats EvidenceBlock items from PreparedEvidence container into context sections."""
        if not evidence.blocks:
            return ""

        context_blocks: List[str] = []
        seen_texts: Set[str] = set()

        primary_blocks = [b for b in evidence.blocks if b.category == "primary"]
        supporting_blocks = [b for b in evidence.blocks if b.category == "supporting"]

        def format_block_list(blocks: List[EvidenceBlock], section_title: Optional[str] = None):
            if not blocks:
                return
            if section_title:
                context_blocks.append(f"[{section_title}]")
            for block_item in blocks:
                cleaned_text = cls._normalize_whitespace(block_item.content)
                if not cleaned_text:
                    continue

                dedup_key = cleaned_text.lower()
                if dedup_key in seen_texts:
                    continue
                seen_texts.add(dedup_key)

                if use_headers:
                    block_str = (
                        f"==========\n"
                        f"Page {block_item.page_number}\n"
                        f"Similarity: {block_item.score:.2f}\n"
                        f"Content:\n"
                        f"{cleaned_text}"
                    )
                else:
                    block_str = f"[Page {block_item.page_number}]\n{cleaned_text}"
                context_blocks.append(block_str)

        # Format primary and supporting evidence groups if multiple categories exist
        if supporting_blocks and primary_blocks:
            format_block_list(primary_blocks, "PRIMARY EVIDENCE")
            format_block_list(supporting_blocks, "SUPPORTING EVIDENCE")
        else:
            format_block_list(evidence.blocks)

        return "\n\n".join(context_blocks)

    @classmethod
    def _normalize_whitespace(cls, text: str) -> str:
        """Removes excessive blank lines, repeated headers, and normalizes space boundaries."""
        if not text:
            return ""
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        normalized = re.sub(r"^(?:==========|Page \d+)\n", "", normalized, flags=re.MULTILINE)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        return normalized.strip()
