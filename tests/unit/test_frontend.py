"""
Unit test for static frontend dashboard endpoint.
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_frontend_index_route() -> None:
    """Verify GET / serves HTML frontend testing dashboard."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "BLUEPRINT" in response.text
    assert "EYE" in response.text
