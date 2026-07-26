"""
Main application entry point for FastAPI backend.
"""

from contextlib import asynccontextmanager
from typing import Dict, AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.core.exceptions import register_exception_handlers
from backend.core.logging import logger
from backend.api.v1.router import api_router
from backend.schemas.health import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown events."""
    logger.info("Starting %s in %s mode", settings.PROJECT_NAME, settings.ENVIRONMENT)
    yield
    logger.info("Shutting down %s", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
if isinstance(settings.ALLOWED_ORIGINS, list):
    for origin in settings.ALLOWED_ORIGINS:
        if origin and origin not in origins and origin != "*":
            origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if "*" not in settings.ALLOWED_ORIGINS else ["*"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Exception Handlers
register_exception_handlers(app)

# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


from pathlib import Path
from fastapi.staticfiles import StaticFiles


# Root level /health endpoint
@app.get("/health", response_model=HealthResponse, status_code=200, tags=["health"])
async def root_health() -> HealthResponse:
    """
    Root level health check endpoint returning system operational status.
    """
    return HealthResponse(status="ok")


# Mount static frontend directory at root / only if a static index.html exists
frontend_index = Path("frontend/index.html")
if frontend_index.exists():
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

