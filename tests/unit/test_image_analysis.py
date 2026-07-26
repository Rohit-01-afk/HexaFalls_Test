"""
Unit tests for Gemini Image Analysis Service.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from backend.core.config import settings
from backend.services.image_analysis_service import ImageAnalysisService


@pytest.mark.anyio
async def test_image_analysis_disabled(tmp_path: Path) -> None:
    """Test image analysis skipped when disabled in settings."""
    service = ImageAnalysisService(api_key="test_key")
    img_file = tmp_path / "page_1.png"
    img_file.write_bytes(b"fake_image_data")

    with patch.object(settings, "ENABLE_IMAGE_ANALYSIS", False):
        result = await service.analyze_page_image(img_file, 1)
        assert result == ""


@pytest.mark.anyio
async def test_image_analysis_no_api_key(tmp_path: Path) -> None:
    """Test image analysis skipped when API key is missing."""
    img_file = tmp_path / "page_1.png"
    img_file.write_bytes(b"fake_image_data")

    with patch.object(settings, "GEMINI_API_KEY", None), \
         patch("os.getenv", return_value=None):
        service = ImageAnalysisService(api_key=None)
        result = await service.analyze_page_image(img_file, 1)
        assert result == ""


@pytest.mark.anyio
async def test_image_analysis_success(tmp_path: Path) -> None:
    """Test successful diagram analysis using Gemini API mock."""
    service = ImageAnalysisService(api_key="valid_key", model="gemini-1.5-flash")
    img_file = tmp_path / "page_1.png"
    img_file.write_bytes(b"fake_image_data")

    mock_gemini_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "Diagram shows a hydraulic pump connected to valve A with label 50 PSI."
                        }
                    ]
                }
            }
        ]
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_gemini_response
    mock_response.raise_for_status = MagicMock()

    mock_post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient.post", mock_post):
        result = await service.analyze_page_image(img_file, 1)
        assert "[Visual Diagram Analysis Page 1]:" in result
        assert "hydraulic pump connected to valve A" in result


@pytest.mark.anyio
async def test_image_analysis_api_error(tmp_path: Path) -> None:
    """Test error handling when Gemini API request fails."""
    service = ImageAnalysisService(api_key="valid_key")
    img_file = tmp_path / "page_1.png"
    img_file.write_bytes(b"fake_image_data")

    with patch("httpx.AsyncClient.post", side_effect=Exception("API Network Timeout")):
        result = await service.analyze_page_image(img_file, 1)
        assert "[Visual Page 1: Image analysis unavailable]" in result
