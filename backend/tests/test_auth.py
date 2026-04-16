"""
Tests for POST /api/v1/auth/refresh.

Strategy: token decode and type-checking happens in the service before any DB call.
Tests that exercise invalid tokens let the real service run (no DB needed).
The success case mocks the DB to return the coach user.
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_db
from app.core.config import settings
from app.core.security import create_refresh_token, create_access_token
from tests.conftest import make_mock_db


def _make_expired_refresh_token(user_id: str) -> str:
    """Create a refresh token that is already expired."""
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() - timedelta(seconds=1),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@pytest.fixture
def http():
    """Plain TestClient with no dependency overrides."""
    return TestClient(app)


@pytest.fixture
def http_with_coach_db(coach_user):
    """
    TestClient with get_db overridden to return the coach when queried.
    Used for the success case where the service needs to look up the user.
    """
    mock_db = make_mock_db(return_value=coach_user)

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# --- Failure cases (no DB needed — token validation fails before DB is hit) ---

def test_refresh_missing_cookie_returns_401(http):
    """No refresh_token cookie → 401."""
    response = http.post("/api/v1/auth/refresh")
    assert response.status_code == 401


def test_refresh_invalid_token_returns_401(http):
    """Garbage string in the cookie → 401."""
    response = http.post("/api/v1/auth/refresh", cookies={"refresh_token": "not.a.jwt"})
    assert response.status_code == 401


def test_refresh_expired_token_returns_401(http, coach_user):
    """Expired refresh token → 401."""
    token = _make_expired_refresh_token(str(coach_user.id))
    response = http.post("/api/v1/auth/refresh", cookies={"refresh_token": token})
    assert response.status_code == 401


def test_refresh_wrong_type_returns_401(http, coach_user):
    """Access token used in place of refresh token → 401."""
    access_token = create_access_token(str(coach_user.id), "coach")
    response = http.post("/api/v1/auth/refresh", cookies={"refresh_token": access_token})
    assert response.status_code == 401


# --- Success case (DB mock needed to return the user) ---

def test_refresh_valid_token_returns_200_and_sets_cookies(http_with_coach_db, coach_user):
    """Valid refresh token → 200 and both auth cookies refreshed."""
    token = create_refresh_token(str(coach_user.id))
    response = http_with_coach_db.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": token},
    )
    assert response.status_code == 200
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


def test_refresh_response_body_contains_user(http_with_coach_db, coach_user):
    """Valid refresh token → response body is the user object."""
    token = create_refresh_token(str(coach_user.id))
    response = http_with_coach_db.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": token},
    )
    body = response.json()
    assert body["email"] == coach_user.email
    assert body["role"] == "coach"
    assert "password" not in body
    assert "password_hash" not in body
