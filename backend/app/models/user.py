"""
User model: represents both coach and client accounts.

Coaches and clients share the same table, differentiated by the `role` column.
The coach_client association table tracks which clients belong to which coaches.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class UserRole(str, enum.Enum):
    """The two account types in ProgramPigeon."""
    coach = "coach"
    client = "client"


# Many-to-many association table linking coaches to their clients
coach_client = Table(
    "coach_client",
    Base.metadata,
    Column("coach_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("client_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    """
    A ProgramPigeon user account.

    A user is either a coach (creates/assigns plans, sends messages) or a
    client (receives plans, sends messages). Role is set at registration and
    cannot be changed.
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Coaches have many clients (and clients have many coaches via backref)
    clients = relationship(
        "User",
        secondary=coach_client,
        primaryjoin="User.id == coach_client.c.coach_id",
        secondaryjoin="User.id == coach_client.c.client_id",
        backref="coaches",
    )

    # Workout plans this coach has created
    workout_plans = relationship("WorkoutPlan", back_populates="coach")

    # Messages this user has sent
    sent_messages = relationship(
        "Message",
        foreign_keys="Message.sender_id",
        back_populates="sender",
    )
