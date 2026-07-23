"""
API endpoint for manual PDF uploads.
"""

from fastapi import APIRouter, File, UploadFile, status

from backend.schemas.upload import UploadResponse
from backend.services.upload_service import UploadService

router = APIRouter()


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF manual",
    description="Accepts, validates, and stores a technical manual in PDF format.",
    responses={
        201: {
            "description": "PDF uploaded and stored successfully",
            "model": UploadResponse,
        },
        400: {"description": "Invalid file extension, invalid MIME type, or bad path"},
        413: {"description": "File size exceeds configured maximum limit"},
        422: {"description": "Validation error (missing file parameter)"},
    },
)
async def upload_pdf(file: UploadFile = File(..., description="PDF technical manual file")) -> UploadResponse:
    """
    Endpoint for uploading technical manual PDFs.
    Routes file directly to UploadService for validation and storage.
    """
    return await UploadService.process_pdf_upload(file)
