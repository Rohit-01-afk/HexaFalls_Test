"""
Pydantic schemas for semantic search engine queries and responses.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    """Request payload model for executing a semantic search query."""

    query: str = Field(..., description="Natural-language search query string")
    top_k: Optional[int] = Field(default=None, description="Maximum number of top results to return")
    document_id: Optional[str] = Field(default=None, description="Optional UUID to filter search results by document")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "how do I replace the cooling fan?",
                "top_k": 5,
                "document_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            }
        }
    )



class SearchResult(BaseModel):
    """Represents a single matched chunk result with similarity score."""

    document_id: str = Field(..., description="UUID of the parent document")
    chunk_id: str = Field(..., description="UUID of the matching chunk")
    page_number: int = Field(..., description="1-indexed page number containing the chunk")
    score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    text: str = Field(..., description="Extracted text content of the matching chunk")


class SearchResponse(BaseModel):
    """Response payload model containing top-k search results sorted by similarity score."""

    query: str = Field(..., description="Original search query string")
    count: int = Field(..., description="Number of results returned")
    results: List[SearchResult] = Field(default_factory=list, description="List of matched search results sorted by score")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "how do I replace the cooling fan?",
                "count": 1,
                "results": [
                    {
                        "document_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                        "chunk_id": "c1234567-58cc-4372-a567-0e02b2c3d479",
                        "page_number": 18,
                        "score": 0.945,
                        "text": "Disconnect cable J7 before removing the cooling fan module.",
                    }
                ],
            }
        }
    )
