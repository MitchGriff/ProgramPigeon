"""
Shared test fixtures for the ProgramPigeon backend test suite.
"""

import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_migrations():
    """
    Patch run_migrations for every test so Alembic never tries to reach a real database.
    Tests that need a database will override this with their own fixtures in a later milestone.
    """
    with patch("app.main.run_migrations"):
        yield
