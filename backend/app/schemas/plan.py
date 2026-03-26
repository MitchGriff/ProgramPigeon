"""
Pydantic schemas for workout plans, workouts, exercises, and plan assignments.

Create schemas are used for request bodies; Response schemas are used for API output.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# --- Exercise ---

class ExerciseCreate(BaseModel):
    """Request body fields for creating a single exercise."""
    name: str
    sets: Optional[int] = None
    reps: Optional[int] = None
    duration_seconds: Optional[int] = None  # For time-based exercises
    notes: Optional[str] = None
    order: int  # 1-based position within the workout


class ExerciseResponse(ExerciseCreate):
    """Exercise data returned from the API."""
    id: uuid.UUID
    workout_id: uuid.UUID

    model_config = {"from_attributes": True}


# --- Workout ---

class WorkoutCreate(BaseModel):
    """Request body fields for creating a workout within a plan."""
    title: str
    order: int  # 1-based position within the plan
    notes: Optional[str] = None
    exercises: List[ExerciseCreate] = []


class WorkoutResponse(BaseModel):
    """Workout data returned from the API, including nested exercises."""
    id: uuid.UUID
    plan_id: uuid.UUID
    title: str
    order: int
    notes: Optional[str]
    exercises: List[ExerciseResponse]

    model_config = {"from_attributes": True}


# --- Workout Plan ---

class WorkoutPlanCreate(BaseModel):
    """Request body for creating a new workout plan."""
    title: str
    description: Optional[str] = None
    workouts: List[WorkoutCreate] = []


class WorkoutPlanResponse(BaseModel):
    """Full workout plan data returned from the API, including nested workouts."""
    id: uuid.UUID
    coach_id: uuid.UUID
    title: str
    description: Optional[str]
    created_at: datetime
    workouts: List[WorkoutResponse]

    model_config = {"from_attributes": True}


# --- Plan Assignment ---

class PlanAssignmentCreate(BaseModel):
    """Request body for assigning a plan to a client."""
    client_id: uuid.UUID


class PlanAssignmentResponse(BaseModel):
    """Confirmation of a plan assignment."""
    id: uuid.UUID
    plan_id: uuid.UUID
    client_id: uuid.UUID
    assigned_at: datetime

    model_config = {"from_attributes": True}
