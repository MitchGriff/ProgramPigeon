"""
Workout plan routes: create, retrieve, and assign plans.

Coaches create plans and assign them to clients.
Clients can view plans assigned to them.
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db, require_coach
from app.models.plan import Exercise, PlanAssignment, Workout, WorkoutPlan
from app.models.user import User
from app.schemas.plan import (
    PlanAssignmentCreate,
    PlanAssignmentResponse,
    WorkoutPlanCreate,
    WorkoutPlanResponse,
)

router = APIRouter()


@router.post("/", response_model=WorkoutPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    data: WorkoutPlanCreate,
    db: AsyncSession = Depends(get_db),
    coach: User = Depends(require_coach),
):
    """
    Create a new workout plan with nested workouts and exercises.

    Only accessible by coaches. The plan is owned by the authenticated coach.

    Args:
        data: Plan title, description, and list of workouts with exercises.
    """
    plan = WorkoutPlan(coach_id=coach.id, title=data.title, description=data.description)
    db.add(plan)
    await db.flush()  # Flush to get plan.id before inserting child rows

    for workout_data in data.workouts:
        workout = Workout(
            plan_id=plan.id,
            title=workout_data.title,
            order=workout_data.order,
            notes=workout_data.notes,
        )
        db.add(workout)
        await db.flush()  # Flush to get workout.id before inserting exercises

        for exercise_data in workout_data.exercises:
            exercise = Exercise(
                workout_id=workout.id,
                name=exercise_data.name,
                sets=exercise_data.sets,
                reps=exercise_data.reps,
                duration_seconds=exercise_data.duration_seconds,
                notes=exercise_data.notes,
                order=exercise_data.order,
            )
            db.add(exercise)

    await db.commit()

    # Reload the plan with all relationships for the response
    result = await db.execute(
        select(WorkoutPlan)
        .where(WorkoutPlan.id == plan.id)
        .options(selectinload(WorkoutPlan.workouts).selectinload(Workout.exercises))
    )
    return result.scalar_one()


@router.get("/", response_model=List[WorkoutPlanResponse])
async def get_plans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return plans relevant to the current user.

    - Coaches see all plans they have created.
    - Clients see all plans assigned to them.
    """
    if current_user.role.value == "coach":
        result = await db.execute(
            select(WorkoutPlan)
            .where(WorkoutPlan.coach_id == current_user.id)
            .options(selectinload(WorkoutPlan.workouts).selectinload(Workout.exercises))
        )
    else:
        result = await db.execute(
            select(WorkoutPlan)
            .join(PlanAssignment, WorkoutPlan.id == PlanAssignment.plan_id)
            .where(PlanAssignment.client_id == current_user.id)
            .options(selectinload(WorkoutPlan.workouts).selectinload(Workout.exercises))
        )
    return result.scalars().all()


@router.get("/{plan_id}", response_model=WorkoutPlanResponse)
async def get_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a single workout plan by ID.

    Coaches can only access their own plans.
    Clients can only access plans assigned to them.

    Raises:
        HTTPException 404: If the plan does not exist or the user lacks access.
    """
    result = await db.execute(
        select(WorkoutPlan)
        .where(WorkoutPlan.id == plan_id)
        .options(selectinload(WorkoutPlan.workouts).selectinload(Workout.exercises))
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    if current_user.role.value == "coach" and plan.coach_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    if current_user.role.value == "client":
        assignment = await db.execute(
            select(PlanAssignment).where(
                PlanAssignment.plan_id == plan_id,
                PlanAssignment.client_id == current_user.id,
            )
        )
        if not assignment.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    return plan


@router.post("/{plan_id}/assign", response_model=PlanAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_plan(
    plan_id: uuid.UUID,
    data: PlanAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    coach: User = Depends(require_coach),
):
    """
    Assign a workout plan to a client.

    The authenticated coach must own the plan.

    Args:
        plan_id: UUID of the plan to assign.
        data: Contains the client_id to assign the plan to.

    Raises:
        HTTPException 404: If the plan does not exist or is not owned by this coach.
        HTTPException 400: If the plan is already assigned to this client.
    """
    result = await db.execute(
        select(WorkoutPlan).where(WorkoutPlan.id == plan_id, WorkoutPlan.coach_id == coach.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    # Check for duplicate assignment
    existing = await db.execute(
        select(PlanAssignment).where(
            PlanAssignment.plan_id == plan_id,
            PlanAssignment.client_id == data.client_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plan already assigned to this client")

    assignment = PlanAssignment(plan_id=plan_id, client_id=data.client_id)
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment
