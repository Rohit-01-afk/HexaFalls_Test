"""
Pydantic schemas for query understanding and intent classification metadata.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class QueryIntentType(str, Enum):
    """Supported intent classification categories for technical queries."""

    DEFINITION = "definition"
    PROCEDURE = "procedure"
    SAFETY = "safety"
    COMPARISON = "comparison"
    DIAGRAM = "diagram"
    TROUBLESHOOTING = "troubleshooting"
    GENERAL = "general"


class QueryIntent(BaseModel):
    """Structured query intent classification metadata payload."""

    intent: QueryIntentType = Field(..., description="Detected query intent category")
    confidence: float = Field(..., description="Deterministic confidence score between 0.0 and 1.0")
    matched_keywords: List[str] = Field(default_factory=list, description="List of keywords or phrase triggers matched during analysis")
    normalized_query: str = Field(..., description="Cleaned, lowercased, and normalized query string")
    reason: str = Field(..., description="Human-readable explanation of detection evidence")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "intent": "procedure",
                "confidence": 0.90,
                "matched_keywords": ["how do i", "replace"],
                "normalized_query": "how do i replace the cooling fan assembly",
                "reason": "Detected intent 'procedure' via matched triggers: 'how do i', 'replace' (confidence: 0.90)",
            }
        }
    )
