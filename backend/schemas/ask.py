"""
Pydantic API schemas for RAG assistant question and response payloads.
"""

from typing import List
from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    """Request payload for RAG question answering endpoint."""

    question: str = Field(..., description="User question string")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "How do I replace the cooling fan assembly?",
            }
        }
    )


class SourceReference(BaseModel):
    """Reference metadata for a source chunk supporting the answer."""

    page: int = Field(..., description="1-indexed page number containing the source chunk")
    chunk_id: str = Field(..., description="UUID of the source chunk")
    score: float = Field(..., description="Similarity score of the source chunk")


class AskResponse(BaseModel):
    """Response payload for RAG question answering endpoint."""

    question: str = Field(..., description="The original user question")
    answer: str = Field(..., description="Grounded AI-generated answer or fallback text")
    sources: List[SourceReference] = Field(default_factory=list, description="Supporting source references from the manual")

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
                    }
                ],
            }
        }
    )
