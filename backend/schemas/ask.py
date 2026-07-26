"""
Pydantic API schemas for RAG assistant question and response payloads.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    """Request payload for RAG question answering endpoint."""

    question: str = Field(..., description="User question string")
    document_id: Optional[str] = Field(default=None, description="Optional document UUID to filter RAG query by document")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "How do I replace the cooling fan assembly?",
                "document_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            }
        }
    )



class SourceReference(BaseModel):
    """Reference metadata for a source chunk supporting the answer."""

    page: int = Field(..., description="1-indexed page number containing the source chunk")
    chunk_id: str = Field(..., description="UUID of the source chunk")
    score: float = Field(..., description="Similarity score of the source chunk")
    document_id: Optional[str] = Field(default=None, description="UUID of the parent document containing the chunk")
    preview: Optional[str] = Field(default=None, description="Preview text snippet of the source chunk")


class RetrievalDiagnostics(BaseModel):
    """Diagnostic statistics for the retrieval and filtering pipeline."""

    raw_count: int = Field(..., description="Number of raw candidate chunks retrieved from vector search")
    deduplicated_count: int = Field(..., description="Number of unique chunks remaining after deduplication")
    filtered_count: int = Field(..., description="Number of chunks meeting the similarity score threshold")
    returned_count: int = Field(..., description="Final count of chunks included in prompt context after limits")
    confidence: str = Field(..., description="Deterministic retrieval confidence rating ('High', 'Medium', 'Low', 'None')")
    filter_reason: Optional[str] = Field(default=None, description="Reason for filtering or empty retrieval if applicable")
    similarity_threshold: float = Field(..., description="Configured minimum similarity score threshold")
    top_k: int = Field(..., description="Configured maximum top_k chunks limit")
    max_context_chars: int = Field(..., description="Configured cumulative context character limit")
    intent: Optional[str] = Field(default=None, description="Detected query intent category ('definition', 'procedure', 'safety', 'comparison', 'diagram', 'troubleshooting', 'general')")
    intent_confidence: Optional[float] = Field(default=None, description="Deterministic confidence score for detected query intent (0.0 to 1.0)")
    matched_keywords: Optional[List[str]] = Field(default_factory=list, description="Keywords or phrase triggers matched during query intent analysis")
    intent_reason: Optional[str] = Field(default=None, description="Human-readable explanation of query intent classification decision")
    selected_chunks: Optional[int] = Field(default=0, description="Count of chunks selected by ContextSelector")
    candidate_chunks: Optional[int] = Field(default=0, description="Count of candidate chunks passed to ContextSelector")
    selection_strategy: Optional[str] = Field(default="none", description="Selection strategy applied by ContextSelector")
    highest_similarity: Optional[float] = Field(default=0.0, description="Highest similarity score among candidate chunks")



class RetrievalMetrics(BaseModel):
    """Pipeline execution latency breakdown in milliseconds."""

    search_ms: float = Field(..., description="Semantic vector search execution time in milliseconds")
    filter_ms: float = Field(..., description="Retrieval filtering execution time in milliseconds")
    prompt_ms: float = Field(..., description="Prompt construction execution time in milliseconds")
    generation_ms: float = Field(..., description="Groq LLM generation execution time in milliseconds")
    total_ms: float = Field(..., description="Total RAG request processing execution time in milliseconds")


class AskResponse(BaseModel):
    """Response payload for RAG question answering endpoint."""

    question: str = Field(..., description="The original user question")
    answer: str = Field(..., description="Grounded AI-generated answer or fallback text")
    sources: List[SourceReference] = Field(default_factory=list, description="Supporting source references from the manual")
    confidence: Optional[str] = Field(default=None, description="Retrieval confidence rating ('High', 'Medium', 'Low', 'None')")
    diagnostics: Optional[RetrievalDiagnostics] = Field(default=None, description="Retrieval filter diagnostic statistics")
    metrics: Optional[RetrievalMetrics] = Field(default=None, description="Pipeline latency performance metrics in milliseconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "How do I replace the cooling fan assembly?",
                "answer": "Disconnect cable J7 before removing the cooling fan assembly from the rear chassis.",
                "sources": [
                    {
                        "page": 18,
                        "chunk_id": "c1234567-58cc-4372-a567-0e02b2c3d479",
                        "score": 0.94,
                        "document_id": "doc-12345",
                        "preview": "Disconnect cable J7 before removing...",
                    }
                ],
                "confidence": "High",
                "diagnostics": {
                    "raw_count": 5,
                    "deduplicated_count": 4,
                    "filtered_count": 2,
                    "returned_count": 1,
                    "confidence": "High",
                    "filter_reason": None,
                    "similarity_threshold": 0.75,
                    "top_k": 5,
                    "max_context_chars": 12000,
                    "intent": "procedure",
                    "intent_confidence": 0.90,
                    "matched_keywords": ["how do i", "replace"],
                    "intent_reason": "Detected intent 'procedure' via matched triggers: 'how do i', 'replace' (confidence: 0.90)",
                },
                "metrics": {
                    "search_ms": 12.5,
                    "filter_ms": 0.4,
                    "prompt_ms": 0.1,
                    "generation_ms": 350.2,
                    "total_ms": 363.2,
                },
            }
        }
    )
