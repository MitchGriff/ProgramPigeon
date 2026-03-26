"""
Imports Base and all ORM models so Alembic autogenerate can detect them.

Only import this module from alembic/env.py — NOT from application code.
Application code should import Base directly from app.db.base and models
from their respective modules to avoid circular imports.
"""

from app.db.base import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.plan import WorkoutPlan, Workout, Exercise, PlanAssignment  # noqa: F401
from app.models.message import Message  # noqa: F401
