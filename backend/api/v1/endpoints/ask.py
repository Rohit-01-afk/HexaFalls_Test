"""
API endpoint for executing Retrieval-Augmented Generation (RAG) question answering.
"""

from fastapi import APIRouter, status

from backend.core.config import settings
from backend.core.logging import logger
from backend.schemas.ask import AskRequest, AskResponse
from backend.services.rag_service import RAGService

router = APIRouter()


@router.post(
    "/ask",
    response_model=AskResponse,
    status_code=status.HTTP_200_OK,
    summary="RAG question answering over technical manuals",
    description="Performs semantic retrieval against technical manuals and generates grounded answers using Groq API (Llama 3.3).",
    responses={
        200: {
            "description": "Question answered successfully using grounded manual context",
            "model": AskResponse,
        },
        422: {"description": "Empty or whitespace-only question payload"},
        503: {"description": "Groq API service unavailable"},
        504: {"description": "Groq API generation timeout"},
    },
)
async def ask_question(request: AskRequest) -> AskResponse:
    """
    Endpoint for asking questions against technical manuals.
    Routes AskRequest payload to RAGService.
    """
    return await RAGService.ask(request)


