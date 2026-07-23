"""
Pydantic schemas for text chunk generation engine.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class Chunk(BaseModel):
    """Represents a discrete text chunk extracted from a manual page."""

    chunk_id: str = Field(..., description="Unique UUID identifier for the chunk")
    document_id: str = Field(..., description="UUID of the parent document")
    page_number: int = Field(..., description="1-indexed page number containing this chunk")
    text: str = Field(..., description="Extracted text content of the chunk")
    start_char: int = Field(..., description="0-indexed start character position in page text")
    end_char: int = Field(..., description="End character position in page text")
    token_count: int = Field(..., description="Approximate token/word count of the chunk text")


class ChunkGenerationResponse(BaseModel):
    """Response model returned after generating text chunks for a document."""

    document_id: str = Field(..., description="UUID of the chunked document")
    chunks: int = Field(..., description="Total number of chunks generated")
    status: str = Field(default="chunked", description="Chunk generation status outcome")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "chunks": 42,
                "status": "chunked",
            }
        }
    )
