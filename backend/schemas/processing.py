"""
Pydantic schemas for PDF processing requests and responses.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ProcessedPage(BaseModel):
    """Represents metadata and extracted content for a processed PDF page."""

    page_id: str = Field(..., description="Unique UUID assigned to the processed page")
    document_id: str = Field(..., description="UUID of the parent document")
    page_number: int = Field(..., description="1-indexed page number within the manual")
    image_path: str = Field(..., description="Relative path to the rendered page image")
    text: str = Field(default="", description="Extracted raw text from the page")


class ProcessResponse(BaseModel):
    """Response model returned after processing a PDF document."""

    document_id: str = Field(..., description="UUID of the processed document")
    pages: int = Field(..., description="Total number of pages processed")
    status: str = Field(default="processed", description="Processing status outcome")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "pages": 12,
                "status": "processed",
            }
        }
    )
