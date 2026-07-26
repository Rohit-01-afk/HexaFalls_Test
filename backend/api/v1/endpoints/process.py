"""
API endpoint for processing uploaded PDF manuals.
"""

from fastapi import APIRouter, Path, status

from backend.schemas.processing import ProcessResponse
from backend.services.pdf_processing_service import PDFProcessingService

router = APIRouter()


@router.post(
    "/process/{document_id}",
    response_model=ProcessResponse,
    status_code=status.HTTP_200_OK,
    summary="Process a PDF manual",
    description="Validates PDF integrity, extracts page text, renders page images, and stores metadata.",
    responses={
        200: {
            "description": "PDF document processed successfully",
            "model": ProcessResponse,
        },
        400: {"description": "Invalid or corrupted PDF file, or document contains zero pages"},
        404: {"description": "Document ID not found in storage"},
    },
)
@router.post(
    "/pdf/process/{document_id}",
    response_model=ProcessResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def process_pdf(
    document_id: str = Path(..., description="Unique UUID identifier of the document to process")
) -> ProcessResponse:
    """
    Endpoint to trigger PDF processing for an uploaded document.
    Routes document_id to PDFProcessingService.
    """
    return await PDFProcessingService.process_document(document_id)
