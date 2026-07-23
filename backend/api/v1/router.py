"""
Central router for API v1 endpoints.
"""

from fastapi import APIRouter
from backend.api.v1.endpoints import chunk, embed, health, process, search, upload


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(upload.router, tags=["upload"])
api_router.include_router(process.router, tags=["process"])
api_router.include_router(chunk.router, tags=["chunk"])
api_router.include_router(embed.router, tags=["embed"])
api_router.include_router(search.router, tags=["search"])





