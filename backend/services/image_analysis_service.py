"""
Service layer for Gemini-powered PDF page diagram and image analysis.
"""

import base64
from pathlib import Path
from typing import Optional
import httpx

from backend.core.config import settings
from backend.core.logging import logger


class ImageAnalysisService:
    """Service for analyzing technical diagrams and figures in PDF page images using Gemini API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL

    async def analyze_page_image(self, image_path: Path, page_number: int) -> str:
        """
        Analyzes a PDF page image to extract textual descriptions of diagrams, schematics, and figures.

        Args:
            image_path: Path to rendered page PNG/JPEG image file.
            page_number: 1-indexed page number.

        Returns:
            Extracted text description of the image content.
        """
        if not settings.ENABLE_IMAGE_ANALYSIS:
            logger.info("Image analysis disabled in settings. Skipping page %d.", page_number)
            return ""

        if not self.api_key:
            logger.info("GEMINI_API_KEY not configured. Skipping Gemini image analysis for page %d.", page_number)
            return ""

        if not image_path.exists():
            logger.warning("Image file %s does not exist for page %d.", image_path, page_number)
            return ""

        try:
            image_bytes = image_path.read_bytes()
            b64_image = base64.b64encode(image_bytes).decode("utf-8")

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

            prompt = (
                f"You are a technical document analyst. Analyze this PDF manual page {page_number}. "
                "Describe any diagrams, schematics, charts, flowcharts, tables, callouts, or visual figures in clear, precise technical detail. "
                "List key components, labels, connection lines, and numerical values present in the visual elements."
            )

            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": b64_image,
                                }
                            },
                        ]
                    }
                ]
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

            candidates = data.get("candidates", [])
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts and "text" in parts[0]:
                    analysis_text = parts[0]["text"].strip()
                    logger.info("Successfully analyzed diagram for page %d using Gemini API.", page_number)
                    return f"[Visual Diagram Analysis Page {page_number}]:\n{analysis_text}"

            logger.warning("Gemini returned empty text response for page %d image analysis.", page_number)
            return ""

        except Exception as err:
            logger.warning("Gemini image analysis failed for page %d: %s", page_number, str(err))
            return f"[Visual Page {page_number}: Image analysis unavailable]"


# Default singleton instance
image_analysis_service = ImageAnalysisService()
