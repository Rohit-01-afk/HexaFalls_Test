"""
Global exception handlers for FastAPI application.
Ensures consistent error responses as specified in API_SPEC.md.
"""

from typing import Any, Dict
from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from backend.core.logging import logger


class OllamaTimeoutError(Exception):
    """Raised when Ollama generation times out."""

    pass


class OllamaConnectionError(Exception):
    """Raised when communication with Ollama host fails (connection refused or network error)."""

    pass


class OllamaResponseError(Exception):
    """Raised when Ollama returns a non-200 status code or malformed JSON payload."""

    pass


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on the FastAPI app instance."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        logger.warning(
            "HTTPException on %s %s: status=%d detail=%s",
            request.method,
            request.url.path,
            exc.status_code,
            exc.detail,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": str(exc.detail), "status": exc.status_code},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning(
            "Validation error on %s %s: %s",
            request.method,
            request.url.path,
            exc.errors(),
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": "Validation error",
                "status": status.HTTP_422_UNPROCESSABLE_CONTENT,
                "details": exc.errors(),
            },
        )

    @app.exception_handler(OllamaTimeoutError)
    async def ollama_timeout_handler(request: Request, exc: OllamaTimeoutError) -> JSONResponse:
        logger.warning("OllamaTimeoutError on %s %s: %s", request.method, request.url.path, str(exc))
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={
                "error": str(exc) or "Generation timed out while communicating with Ollama server.",
                "status": status.HTTP_504_GATEWAY_TIMEOUT,
            },
        )

    @app.exception_handler(OllamaConnectionError)
    async def ollama_connection_handler(request: Request, exc: OllamaConnectionError) -> JSONResponse:
        logger.warning("OllamaConnectionError on %s %s: %s", request.method, request.url.path, str(exc))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": str(exc) or "Ollama service is unavailable.",
                "status": status.HTTP_503_SERVICE_UNAVAILABLE,
            },
        )

    @app.exception_handler(OllamaResponseError)
    async def ollama_response_handler(request: Request, exc: OllamaResponseError) -> JSONResponse:
        logger.error("OllamaResponseError on %s %s: %s", request.method, request.url.path, str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": str(exc) or "Ollama returned a malformed response.",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled exception on %s %s: %s",
            request.method,
            request.url.path,
            str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
        )

