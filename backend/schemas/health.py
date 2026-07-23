"""
Pydantic schemas for health check endpoint.
"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(default="ok", description="Application status indicator")
