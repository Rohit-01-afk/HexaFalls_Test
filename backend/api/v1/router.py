"""
Central router for API v1 endpoints.
"""

from fastapi import APIRouter
from backend.api.v1.endpoints import health, upload


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(upload.router, tags=["upload"])

