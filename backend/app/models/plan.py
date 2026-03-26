"""
Workout plan models: WorkoutPlan, Workout, Exercise, PlanAssignment.

Hierarchy:
  WorkoutPlan  (created by a coach, assigned to clients)
    └── Workout  (a single session, e.g. "Day 1 - Upper Body")
          └── Exercise  (a single movement, e.g. "Bench Press 3x8")

PlanAssignment records which client has been assigned a given plan.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class WorkoutPlan(Base):
    """
    A named collection of workouts created by a coach.
    Can be assigned to one or more clients via PlanAssignment.
    """

    __tablename__ = "workout_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coach_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    coach = relationship("User", back_populates="workout_plans")
    workouts = relationship("Workout", back_populates="plan", order_by="Workout.order", cascade="all, delete-orphan")
    assignments = relationship("PlanAssignment", back_populates="plan", cascade="all, delete-orphan")


class Workout(Base):
    """
    A single workout session within a plan (e.g. "Day 1 - Push").
    `order` determines its position in the plan sequence.
    """

    __tablename__ = "workouts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("workout_plans.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    order = Column(Integer, nullable=False)  # 1-based position within the plan
    notes = Column(Text, nullable=True)

    plan = relationship("WorkoutPlan", back_populates="workouts")
    exercises = relationship("Exercise", back_populates="workout", order_by="Exercise.order", cascade="all, delete-orphan")


class Exercise(Base):
    """
    A single exercise within a workout.

    Either `sets`/`reps` (strength) or `duration_seconds` (cardio/time-based)
    should be populated — both are optional to support flexible programming.
    """

    __tablename__ = "exercises"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workout_id = Column(UUID(as_uuid=True), ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    sets = Column(Integer, nullable=True)
    reps = Column(Integer, nullable=True)
    duration_seconds = Column(Integer, nullable=True)  # For time-based exercises
    notes = Column(Text, nullable=True)
    order = Column(Integer, nullable=False)  # 1-based position within the workout

    workout = relationship("Workout", back_populates="exercises")


class PlanAssignment(Base):
    """
    Records that a coach has assigned a workout plan to a specific client.
    A plan can be assigned to multiple clients; a client can have multiple plans.
    """

    __tablename__ = "plan_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("workout_plans.id", ondelete="CASCADE"), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    plan = relationship("WorkoutPlan", back_populates="assignments")
    client = relationship("User")
