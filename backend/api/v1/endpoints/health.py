"""
Health check API endpoint.
"""

from fastapi import APIRouter
from backend.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, status_code=200)
async def get_health() -> HealthResponse:
    """
    Health check endpoint returning system operational status.
    """
    return HealthResponse(status="ok")
