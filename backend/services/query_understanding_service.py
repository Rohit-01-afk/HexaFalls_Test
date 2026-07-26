"""
Service layer for deterministic query intent analysis and metadata classification.
"""

import re
from typing import Dict, List, Tuple
from backend.core.logging import logger
from backend.schemas.query_intent import QueryIntent, QueryIntentType


class QueryUnderstandingService:
    """
    Analyzes technical user queries to extract structured intent metadata,
    confidence ratings, and matched keyword triggers.
    Does NOT perform vector retrieval, Gemini generation, or prompt modification.
    """

    # Category pattern triggers: (intent_type, phrase_patterns, keyword_triggers)
    # Phrase patterns carry base weight 0.85; word triggers carry base weight 0.70.
    TRIGGER_RULES: List[Tuple[QueryIntentType, List[str], List[str]]] = [
        (
            QueryIntentType.SAFETY,
            ["safety precautions", "protective equipment", "hazard warning", "safety warning"],
            ["warning", "caution", "danger", "hazard", "safety", "precaution", "protective", "risk"],
        ),
        (
            QueryIntentType.PROCEDURE,
            ["how do i", "how to", "steps to", "instructions for", "how can i"],
            ["replace", "install", "configure", "setup", "remove", "clean", "assembly", "procedure", "step"],
        ),
        (
            QueryIntentType.TROUBLESHOOTING,
            ["how to fix", "error code", "reason for failure", "why is"],
            ["problem", "issue", "fix", "error", "failure", "fault", "troubleshoot", "malfunction", "breakdown"],
        ),
        (
            QueryIntentType.DIAGRAM,
            ["show figure", "circuit diagram", "flowchart of", "schematic of"],
            ["figure", "diagram", "circuit", "flowchart", "schematic", "drawing", "illustration", "pinout"],
        ),
        (
            QueryIntentType.COMPARISON,
            ["difference between", "compared to", "versus", "comparison of"],
            ["difference", "compare", "versus", "vs", "differ", "distinction"],
        ),
        (
            QueryIntentType.DEFINITION,
            ["what is", "what are", "define", "meaning of", "explanation of"],
            ["definition", "overview", "concept", "description"],
        ),
    ]

    @classmethod
    def _normalize_query(cls, raw_query: str) -> str:
        """Cleans, lowercases, and normalizes a raw query string."""
        if not raw_query:
            return ""
        # Lowercase and strip leading/trailing whitespace
        cleaned = raw_query.strip().lower()
        # Replace non-alphanumeric chars (except whitespace) with spaces for keyword matching
        cleaned = re.sub(r"[^\w\s]", " ", cleaned)
        # Collapse multiple spaces into a single space
        return re.sub(r"\s+", " ", cleaned).strip()

    @classmethod
    def analyze_query(cls, query: str) -> QueryIntent:
        """
        Analyzes natural-language query and returns a structured QueryIntent object.

        Args:
            query: Raw user query string.

        Returns:
            QueryIntent containing intent type, confidence score, matched keywords,
            normalized query, and human-readable detection reason.
        """
        raw_q = query or ""
        normalized_q = cls._normalize_query(raw_q)

        if not normalized_q:
            logger.info("Empty query provided to QueryUnderstandingService. Defaulting to general intent.")
            return QueryIntent(
                intent=QueryIntentType.GENERAL,
                confidence=0.0,
                matched_keywords=[],
                normalized_query="",
                reason="Empty query provided; fell back to general category.",
            )

        # Word tokens for single-word matching
        words = set(normalized_q.split())

        best_intent: QueryIntentType = QueryIntentType.GENERAL
        best_score: float = 0.0
        best_matches: List[str] = []

        for intent_type, phrases, keywords in cls.TRIGGER_RULES:
            matched_phrases = [p for p in phrases if p in normalized_q]
            matched_kws = [
                k for k in keywords
                if k in words or any(w.startswith(k) for w in words if len(k) >= 3)
            ]

            # Deduplicate matched triggers while preserving match order
            all_matches: List[str] = []
            for m in matched_phrases + matched_kws:
                if m not in all_matches:
                    all_matches.append(m)

            if not all_matches:
                continue

            # Calculate base score based on strongest match type
            base_score = 0.85 if matched_phrases else 0.70
            # Multi-trigger evidence accumulation (+0.05 for each additional match)
            total_score = min(1.0, base_score + 0.05 * (len(all_matches) - 1))
            total_score = round(total_score, 2)

            if total_score > best_score:
                best_score = total_score
                best_intent = intent_type
                best_matches = all_matches

        if best_intent == QueryIntentType.GENERAL or best_score == 0.0:
            logger.info(
                "Query intent analyzed: original='%s', normalized='%s', intent='general', confidence=0.00, keywords=[]",
                raw_q,
                normalized_q,
            )
            return QueryIntent(
                intent=QueryIntentType.GENERAL,
                confidence=0.0,
                matched_keywords=[],
                normalized_query=normalized_q,
                reason="No domain intent keywords matched; fell back to general category.",
            )

        matched_str = ", ".join(f"'{m}'" for m in best_matches)
        reason = (
            f"Detected intent '{best_intent.value}' via matched triggers: {matched_str} "
            f"(confidence: {best_score:.2f})"
        )

        logger.info(
            "Query intent analyzed: original='%s', normalized='%s', intent='%s', confidence=%.2f, keywords=%s",
            raw_q,
            normalized_q,
            best_intent.value,
            best_score,
            best_matches,
        )

        return QueryIntent(
            intent=best_intent,
            confidence=best_score,
            matched_keywords=best_matches,
            normalized_query=normalized_q,
            reason=reason,
        )
