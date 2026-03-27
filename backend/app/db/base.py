"""
Declarative base for all SQLAlchemy ORM models.

All models must inherit from Base. This module intentionally contains only
the Base class to avoid circular imports (models import Base; Alembic model
discovery is handled in app/db/base_all.py).
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass
