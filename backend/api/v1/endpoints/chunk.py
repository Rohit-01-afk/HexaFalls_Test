"""
API endpoint for generating text chunks from document metadata.
"""

from fastapi import APIRouter, Path, status

from backend.schemas.chunking import ChunkGenerationResponse
from backend.services.chunking_service import ChunkingService

router = APIRouter()


@router.post(
    "/chunk/{document_id}",
    response_model=ChunkGenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate text chunks for a document",
    description="Splits document page text into sliding-window text chunks preserving page boundaries.",
    responses={
        200: {
            "description": "Chunks generated successfully",
            "model": ChunkGenerationResponse,
        },
        400: {"description": "Document metadata is empty, invalid, or contains no pages"},
        404: {"description": "Document metadata not found"},
    },
)
async def chunk_document(
    document_id: str = Path(..., description="Unique UUID identifier of the document to chunk")
) -> ChunkGenerationResponse:
    """
    Endpoint to trigger text chunk generation for a processed document.
    Routes document_id to ChunkingService.
    """
    return await ChunkingService.generate_chunks(document_id)
