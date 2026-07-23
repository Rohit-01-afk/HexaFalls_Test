"""
API endpoint for executing semantic search queries.
"""

from fastapi import APIRouter, status

from backend.schemas.search import SearchRequest, SearchResponse
from backend.services.search_service import SearchService

router = APIRouter()


@router.post(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic search across technical manual chunks",
    description="Performs dense vector similarity search against ChromaDB using natural-language queries.",
    responses={
        200: {
            "description": "Semantic search executed successfully",
            "model": SearchResponse,
        },
        400: {"description": "Empty query string or invalid top_k boundary"},
    },
)
async def search_manuals(request: SearchRequest) -> SearchResponse:
    """
    Endpoint for performing semantic vector search on indexed document chunks.
    Routes SearchRequest to SearchService.
    """
    return await SearchService.search(request)
