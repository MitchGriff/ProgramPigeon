"""
Tests for the /health endpoint.
"""

from fastapi.testclient import TestClient
from app.main import app


def test_health_check_returns_200():
    """GET /health should return 200 with status ok."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_response_body():
    """GET /health should return {"status": "ok"}."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.json() == {"status": "ok"}
