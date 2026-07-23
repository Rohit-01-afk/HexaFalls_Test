"""
Pydantic schemas for upload API endpoint responses.
"""

from pydantic import BaseModel, ConfigDict, Field


class UploadResponse(BaseModel):
    """Response model returned after a successful document upload."""

    document_id: str = Field(..., description="Unique UUID assigned to the uploaded document")
    filename: str = Field(..., description="Original filename of the uploaded file")
    stored_filename: str = Field(..., description="Sanitized filename used for storage")
    size: int = Field(..., description="Size of the uploaded file in bytes")
    status: str = Field(default="uploaded", description="Status of the upload operation")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "filename": "manual.pdf",
                "stored_filename": "f47ac10b-58cc-4372-a567-0e02b2c3d479_manual.pdf",
                "size": 1048576,
                "status": "uploaded",
            }
        }
    )
