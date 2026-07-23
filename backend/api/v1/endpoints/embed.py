"""
API endpoint for generating embeddings and vector indexing in ChromaDB.
"""

from fastapi import APIRouter, Path, status

from backend.schemas.embedding import EmbeddingResponse
from backend.services.embedding_service import EmbeddingService

router = APIRouter()


@router.post(
    "/embed/{document_id}",
    response_model=EmbeddingResponse,
    status_code=status.HTTP_200_OK,
    summary="Embed and index document chunks",
    description="Generates vector embeddings for document chunks using SentenceTransformers and indexes them into ChromaDB.",
    responses={
        200: {
            "description": "Document chunks embedded and indexed successfully",
            "model": EmbeddingResponse,
        },
        400: {"description": "Chunk data is empty or invalid"},
        404: {"description": "Chunk metadata not found for document"},
    },
)
async def embed_document(
    document_id: str = Path(..., description="Unique UUID identifier of the document to embed")
) -> EmbeddingResponse:
    """
    Endpoint to trigger embedding generation and vector store indexing.
    Routes document_id to EmbeddingService.
    """
    return await EmbeddingService.generate_and_index_embeddings(document_id)
