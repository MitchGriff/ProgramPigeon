"""
Tests for POST /api/v1/users/clients/by-email.

Strategy: override get_current_user to simulate a coach, override get_db to
return the mock client user. Each test sets up overrides independently.
"""

import uuid
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_db, get_current_user
from app.models.user import User, UserRole
from tests.conftest import make_mock_db


@pytest.fixture
def http_as_coach(coach_user, client_user):
    """
    TestClient acting as coach_user, with DB returning client_user on lookup.
    """
    mock_db = make_mock_db(return_value=client_user)

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: coach_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def http_as_coach_empty_db(coach_user):
    """
    TestClient acting as coach_user, with DB returning None (no user found).
    """
    mock_db = make_mock_db(return_value=None)

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: coach_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def http_as_coach_db_returns_another_coach(coach_user):
    """
    TestClient acting as coach_user, with DB returning a user who is also a coach.
    Used to verify that adding a coach-role user is rejected.
    """
    another_coach = User()
    another_coach.id = uuid.UUID("00000000-0000-0000-0000-000000000003")
    another_coach.email = "another@coach.com"
    another_coach.name = "Another Coach"
    another_coach.role = UserRole.coach
    another_coach.created_at = datetime(2026, 1, 1, 0, 0, 0)
    another_coach.clients = []

    mock_db = make_mock_db(return_value=another_coach)

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: coach_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def http_as_coach_client_already_added(coach_user, client_user):
    """
    TestClient acting as coach_user who already has client_user on their roster.
    """
    coach_user.clients = [client_user]
    mock_db = make_mock_db(return_value=client_user)

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: coach_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def http_as_client(client_user):
    """
    TestClient acting as a client (not a coach). Used to verify 403 enforcement.
    """
    mock_db = make_mock_db()

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: client_user
    yield TestClient(app)
    app.dependency_overrides.clear()


# --- Tests ---

def test_add_client_by_email_success(http_as_coach, client_user):
    """Coach adds a client by valid email → 201 and client data returned."""
    response = http_as_coach.post(
        "/api/v1/users/clients/by-email",
        json={"email": client_user.email},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == client_user.email
    assert body["role"] == "client"
    assert "password_hash" not in body


def test_add_client_email_not_found_returns_404(http_as_coach_empty_db):
    """Email doesn't match any account → 404."""
    response = http_as_coach_empty_db.post(
        "/api/v1/users/clients/by-email",
        json={"email": "ghost@nowhere.com"},
    )
    assert response.status_code == 404


def test_add_client_coach_email_returns_404(http_as_coach_db_returns_another_coach):
    """Email belongs to a coach, not a client → 404 (no role leakage)."""
    response = http_as_coach_db_returns_another_coach.post(
        "/api/v1/users/clients/by-email",
        json={"email": "another@coach.com"},
    )
    assert response.status_code == 404


def test_add_client_already_linked_returns_400(http_as_coach_client_already_added, client_user):
    """Client already on roster → 400."""
    response = http_as_coach_client_already_added.post(
        "/api/v1/users/clients/by-email",
        json={"email": client_user.email},
    )
    assert response.status_code == 400


def test_add_client_by_client_returns_403(http_as_client, client_user):
    """Only coaches can add clients → 403 for client callers."""
    response = http_as_client.post(
        "/api/v1/users/clients/by-email",
        json={"email": client_user.email},
    )
    assert response.status_code == 403
