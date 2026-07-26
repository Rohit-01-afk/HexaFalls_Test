"""
Global exception handlers for FastAPI application.
Ensures consistent error responses as specified in API_SPEC.md.
"""

from typing import Any, Dict
from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from backend.core.logging import logger


class GroqTimeoutError(Exception):
    """Raised when Groq API generation times out."""

    pass


class GroqConnectionError(Exception):
    """Raised when communication with Groq API fails (connection refused, missing key, or network error)."""

    pass


class GroqResponseError(Exception):
    """Raised when Groq returns a non-200 status code or malformed JSON payload."""

    pass


class GeminiTimeoutError(Exception):
    """Raised when Gemini API generation times out."""

    pass


class GeminiConnectionError(Exception):
    """Raised when communication with Gemini API fails (connection refused or network error)."""

    pass


class GeminiResponseError(Exception):
    """Raised when Gemini returns a non-200 status code or malformed JSON payload."""

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

    @app.exception_handler(GroqTimeoutError)
    async def groq_timeout_handler(request: Request, exc: GroqTimeoutError) -> JSONResponse:
        logger.warning("GroqTimeoutError on %s %s: %s", request.method, request.url.path, str(exc))
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={
                "error": str(exc) or "Generation timed out while communicating with Groq API.",
                "status": status.HTTP_504_GATEWAY_TIMEOUT,
            },
        )

    @app.exception_handler(GroqConnectionError)
    async def groq_connection_handler(request: Request, exc: GroqConnectionError) -> JSONResponse:
        logger.warning("GroqConnectionError on %s %s: %s", request.method, request.url.path, str(exc))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": str(exc) or "Groq API service is unavailable.",
                "status": status.HTTP_503_SERVICE_UNAVAILABLE,
            },
        )

    @app.exception_handler(GroqResponseError)
    async def groq_response_handler(request: Request, exc: GroqResponseError) -> JSONResponse:
        logger.error("GroqResponseError on %s %s: %s", request.method, request.url.path, str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": str(exc) or "Groq API returned a malformed response.",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
        )

    @app.exception_handler(GeminiTimeoutError)
    async def gemini_timeout_handler(request: Request, exc: GeminiTimeoutError) -> JSONResponse:
        logger.warning("GeminiTimeoutError on %s %s: %s", request.method, request.url.path, str(exc))
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={
                "error": str(exc) or "Generation timed out while communicating with Gemini API.",
                "status": status.HTTP_504_GATEWAY_TIMEOUT,
            },
        )

    @app.exception_handler(GeminiConnectionError)
    async def gemini_connection_handler(request: Request, exc: GeminiConnectionError) -> JSONResponse:
        logger.warning("GeminiConnectionError on %s %s: %s", request.method, request.url.path, str(exc))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": str(exc) or "Gemini API service is unavailable.",
                "status": status.HTTP_503_SERVICE_UNAVAILABLE,
            },
        )

    @app.exception_handler(GeminiResponseError)
    async def gemini_response_handler(request: Request, exc: GeminiResponseError) -> JSONResponse:
        logger.error("GeminiResponseError on %s %s: %s", request.method, request.url.path, str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": str(exc) or "Gemini API returned a malformed response.",
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

