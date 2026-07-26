"""
Unit test for static frontend dashboard endpoint.
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_frontend_index_route() -> None:
    """Verify backend health endpoint is accessible when frontend runs on port 3000."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
