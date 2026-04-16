"""
Shared test fixtures for the ProgramPigeon backend test suite.
"""

import uuid
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.user import User, UserRole


@pytest.fixture(autouse=True)
def mock_migrations():
    """
    Patch run_migrations for every test so Alembic never tries to reach a real database.
    """
    with patch("app.main.run_migrations"):
        yield


@pytest.fixture
def coach_user():
    """A mock coach User — use wherever a logged-in coach is needed."""
    user = User()
    user.id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    user.email = "coach@test.com"
    user.name = "Test Coach"
    user.role = UserRole.coach
    user.created_at = datetime(2026, 1, 1, 0, 0, 0)
    user.clients = []
    return user


@pytest.fixture
def client_user():
    """A mock client User — use wherever a target client is needed."""
    user = User()
    user.id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    user.email = "client@test.com"
    user.name = "Test Client"
    user.role = UserRole.client
    user.created_at = datetime(2026, 1, 1, 0, 0, 0)
    user.clients = []
    return user


def make_mock_db(return_value=None):
    """
    Build a mock AsyncSession that returns `return_value` for any .execute() call.
    commit() and refresh() are no-ops by default.

    Args:
        return_value: What scalar_one_or_none() returns. Pass None to simulate not found.
    """
    session = AsyncMock()
    # Use MagicMock for the result — scalar_one_or_none() is synchronous,
    # so AsyncMock would return a coroutine instead of the value when called.
    result = MagicMock()
    result.scalar_one_or_none.return_value = return_value
    session.execute.return_value = result
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session
