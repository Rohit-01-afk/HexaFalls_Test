"""
Pydantic schemas for embedding generation and vector indexing engine.
"""

from pydantic import BaseModel, ConfigDict, Field


class EmbeddingResponse(BaseModel):
    """Response model returned after generating embeddings and indexing chunks into ChromaDB."""

    document_id: str = Field(..., description="UUID of the indexed document")
    indexed_chunks: int = Field(..., description="Total number of chunks successfully indexed in ChromaDB")
    collection: str = Field(..., description="Name of the ChromaDB collection where vectors are stored")
    status: str = Field(default="indexed", description="Vector indexing status outcome")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "indexed_chunks": 42,
                "collection": "manual_chunks",
                "status": "indexed",
            }
        }
    )
