# M3: Workout Builder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the workout builder — a plan library with full CRUD and a per-client calendar where plans are applied and individual workouts can be created and edited.

**Architecture:** Two new DB tables (`scheduled_workouts`, `scheduled_exercises`) store client-specific workout instances copied from plan templates on assignment. The plan template `Exercise` model is migrated to a label + free-text description model. All schedule logic lives in a new service and router registered under `/api/v1/clients`.

**Tech Stack:** FastAPI, SQLAlchemy async, Alembic, Pydantic, React, TypeScript, CSS Modules

---

## File Map

### Backend — Modified
- `backend/app/models/plan.py` — update `Exercise` (add `label`, `description`; drop `sets`, `reps`, `duration_seconds`, `notes`), add `is_rest_day` to `Workout`, add `start_date` to `PlanAssignment`; add `ScheduledWorkout`, `ScheduledExercise` models
- `backend/app/schemas/plan.py` — update `ExerciseCreate`, `ExerciseResponse`, `WorkoutCreate`, `WorkoutResponse`, `PlanAssignmentCreate`
- `backend/app/api/v1/plans.py` — update `create_plan` for new model; add `PUT /{id}`, `DELETE /{id}`; update `assign_plan` to accept `start_date` and call schedule service
- `backend/app/db/base_all.py` — import `ScheduledWorkout`, `ScheduledExercise`
- `backend/app/main.py` — register schedule router

### Backend — New
- `backend/app/schemas/schedule.py` — `ScheduledExerciseCreate/Response`, `ScheduledWorkoutCreate/Update/Response`
- `backend/app/services/schedule.py` — `instantiate_plan_for_client` service function
- `backend/app/api/v1/schedule.py` — client schedule CRUD router
- `backend/tests/test_plans.py` — plan CRUD + assignment tests
- `backend/tests/test_schedule.py` — schedule endpoint tests

### Frontend — Modified
- `frontend/src/types/plan.ts` — update `Exercise`, `Workout`, `ExercisePayload`, `WorkoutPayload`
- `frontend/src/api/plans.ts` — add `updatePlan`, `deletePlan`; update `assignPlan` to accept `startDate`
- `frontend/src/pages/PlanDetailPage.tsx` — update exercise display; add Edit/Delete buttons; add `start_date` to assign form
- `frontend/src/pages/ClientsPage.tsx` — link each client to `/clients/:id`
- `frontend/src/App.tsx` — add routes for `/plans/new`, `/plans/:id/edit`, `/clients/:id`

### Frontend — New
- `frontend/src/types/schedule.ts`
- `frontend/src/api/schedule.ts`
- `frontend/src/hooks/useSchedule.ts`
- `frontend/src/components/PlanBuilderForm.tsx`
- `frontend/src/components/PlanBuilderForm.module.css`
- `frontend/src/pages/CreatePlanPage.tsx`
- `frontend/src/pages/CreatePlanPage.module.css`
- `frontend/src/pages/EditPlanPage.tsx`
- `frontend/src/pages/ClientProgramPage.tsx`
- `frontend/src/pages/ClientProgramPage.module.css`

---

### Task 1: Update Exercise, Workout, PlanAssignment models and schemas

**Files:**
- Modify: `backend/app/models/plan.py`
- Modify: `backend/app/schemas/plan.py`

- [ ] **Step 1: Update `Exercise` model**

Replace the body of the `Exercise` class in `backend/app/models/plan.py`:

```python
class Exercise(Base):
    """
    A single exercise block within a workout.
    `label` identifies position and superset grouping (A, B, B1, B2...).
    `description` is free-text programming notes (sets, reps, tempo, rest, etc.).
    """

    __tablename__ = "exercises"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workout_id = Column(UUID(as_uuid=True), ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False)
    label = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, nullable=False)

    workout = relationship("Workout", back_populates="exercises")
```

- [ ] **Step 2: Add `is_rest_day` to `Workout` model**

Add to the `Workout` class after the `order` column (also add `Boolean` to the SQLAlchemy imports at the top):

```python
# Add to imports at top of file:
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

# Add to Workout class after `order`:
is_rest_day = Column(Boolean, default=False, nullable=False)
```

- [ ] **Step 3: Add `start_date` to `PlanAssignment` model**

Add to imports and to the `PlanAssignment` class:

```python
# Add to imports at top of file:
from datetime import date, datetime
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text

# Add to PlanAssignment class after `client_id`:
start_date = Column(Date, nullable=False)
```

- [ ] **Step 4: Update `ExerciseCreate` and `ExerciseResponse` schemas**

Replace both classes in `backend/app/schemas/plan.py`:

```python
class ExerciseCreate(BaseModel):
    """Request body fields for creating a single exercise block."""
    label: str
    name: str
    description: Optional[str] = None
    order: int


class ExerciseResponse(BaseModel):
    """Exercise block data returned from the API."""
    id: uuid.UUID
    workout_id: uuid.UUID
    label: str
    name: str
    description: Optional[str]
    order: int

    model_config = {"from_attributes": True}
```

- [ ] **Step 5: Update `WorkoutCreate` and `WorkoutResponse` schemas**

Replace both classes:

```python
class WorkoutCreate(BaseModel):
    """Request body fields for creating a workout within a plan."""
    title: Optional[str] = None
    order: int
    notes: Optional[str] = None
    is_rest_day: bool = False
    exercises: List[ExerciseCreate] = []


class WorkoutResponse(BaseModel):
    """Workout data returned from the API, including nested exercise blocks."""
    id: uuid.UUID
    plan_id: uuid.UUID
    title: Optional[str]
    order: int
    notes: Optional[str]
    is_rest_day: bool
    exercises: List[ExerciseResponse]

    model_config = {"from_attributes": True}
```

- [ ] **Step 6: Update `PlanAssignmentCreate` schema**

Replace the class (add `from datetime import date` to imports):

```python
from datetime import date, datetime

class PlanAssignmentCreate(BaseModel):
    """Request body for assigning a plan to a client."""
    client_id: uuid.UUID
    start_date: date
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/plan.py backend/app/schemas/plan.py
git commit -m "feat: migrate exercise model to label+description, add is_rest_day and start_date"
```

---

### Task 2: Add ScheduledWorkout and ScheduledExercise models

**Files:**
- Modify: `backend/app/models/plan.py`
- Modify: `backend/app/db/base_all.py`

- [ ] **Step 1: Add `ScheduledWorkout` and `ScheduledExercise` to `plan.py`**

Append to the bottom of `backend/app/models/plan.py`:

```python
class ScheduledWorkout(Base):
    """
    A client-specific workout instance on a specific calendar date.
    Created either by plan assignment (source_plan_id set) or directly by the coach.
    Once created, it is independent of the source plan template.
    """

    __tablename__ = "scheduled_workouts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    coach_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    title = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    is_rest_day = Column(Boolean, default=False, nullable=False)
    source_plan_id = Column(UUID(as_uuid=True), ForeignKey("workout_plans.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    client = relationship("User", foreign_keys=[client_id])
    coach = relationship("User", foreign_keys=[coach_id])
    exercises = relationship(
        "ScheduledExercise",
        back_populates="scheduled_workout",
        order_by="ScheduledExercise.order",
        cascade="all, delete-orphan",
    )


class ScheduledExercise(Base):
    """
    An exercise block within a ScheduledWorkout.
    Copied from the plan template on assignment; editable independently.
    """

    __tablename__ = "scheduled_exercises"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheduled_workout_id = Column(
        UUID(as_uuid=True), ForeignKey("scheduled_workouts.id", ondelete="CASCADE"), nullable=False
    )
    label = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, nullable=False)

    scheduled_workout = relationship("ScheduledWorkout", back_populates="exercises")
```

- [ ] **Step 2: Register new models in `base_all.py`**

Add to `backend/app/db/base_all.py`:

```python
from app.models.plan import Exercise, PlanAssignment, ScheduledExercise, ScheduledWorkout, Workout, WorkoutPlan  # noqa: F401
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/plan.py backend/app/db/base_all.py
git commit -m "feat: add ScheduledWorkout and ScheduledExercise models"
```

---

### Task 3: Create and apply Alembic migrations

**Files:**
- Create: `backend/alembic/versions/<hash>_update_exercise_model.py` (autogenerated)
- Create: `backend/alembic/versions/<hash>_add_scheduled_tables.py` (autogenerated)

- [ ] **Step 1: Reset DB to avoid column-drop conflicts**

```bash
docker-compose down -v
docker-compose up -d
```

Wait ~15 seconds for the DB healthcheck to pass, then verify:

```bash
docker ps
```

Expected: `programpigeon-backend-1`, `programpigeon-db-1`, `programpigeon-frontend-1` all running.

- [ ] **Step 2: Generate migration 1 — modify existing tables**

```bash
docker-compose exec backend alembic revision --autogenerate -m "update_exercise_model_add_scheduled_columns"
```

Expected output: `Generating .../alembic/versions/<hash>_update_exercise_model_add_scheduled_columns.py`

- [ ] **Step 3: Generate migration 2 — create scheduled tables**

```bash
docker-compose exec backend alembic revision --autogenerate -m "add_scheduled_workouts_and_exercises"
```

Expected output: `Generating .../alembic/versions/<hash>_add_scheduled_workouts_and_exercises.py`

- [ ] **Step 4: Apply both migrations**

```bash
docker-compose exec backend alembic upgrade head
```

Expected: two revision hashes printed, ending with `Running upgrade ... -> ..., add_scheduled_workouts_and_exercises`

- [ ] **Step 5: Verify tables**

```bash
docker-compose exec db psql -U programpigeon -d programpigeon -c "\d exercises"
```

Expected: columns `id`, `workout_id`, `label`, `name`, `description`, `order` — no `sets`, `reps`, `duration_seconds`, `notes`.

```bash
docker-compose exec db psql -U programpigeon -d programpigeon -c "\d scheduled_workouts"
```

Expected: columns `id`, `client_id`, `coach_id`, `date`, `title`, `notes`, `is_rest_day`, `source_plan_id`, `created_at`.

- [ ] **Step 6: Commit**

```bash
git add backend/alembic/versions/
git commit -m "chore: alembic migrations for exercise model update and scheduled tables"
```

---

### Task 4: Add schedule schemas

**Files:**
- Create: `backend/app/schemas/schedule.py`

- [ ] **Step 1: Create `schedule.py` schemas**

```python
"""
Pydantic schemas for client-scheduled workouts and exercise blocks.
"""

import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class ScheduledExerciseCreate(BaseModel):
    """Fields for creating a scheduled exercise block."""
    label: str
    name: str
    description: Optional[str] = None
    order: int


class ScheduledExerciseResponse(BaseModel):
    """Scheduled exercise block data returned from the API."""
    id: uuid.UUID
    scheduled_workout_id: uuid.UUID
    label: str
    name: str
    description: Optional[str]
    order: int

    model_config = {"from_attributes": True}


class ScheduledWorkoutCreate(BaseModel):
    """Request body for creating a one-off scheduled workout."""
    date: date
    title: Optional[str] = None
    notes: Optional[str] = None
    is_rest_day: bool = False
    exercises: List[ScheduledExerciseCreate] = []


class ScheduledWorkoutUpdate(BaseModel):
    """Request body for updating a scheduled workout (wholesale replace of exercises)."""
    title: Optional[str] = None
    notes: Optional[str] = None
    is_rest_day: bool = False
    exercises: List[ScheduledExerciseCreate] = []


class ScheduledWorkoutResponse(BaseModel):
    """Scheduled workout data returned from the API."""
    id: uuid.UUID
    client_id: uuid.UUID
    coach_id: uuid.UUID
    date: date
    title: Optional[str]
    notes: Optional[str]
    is_rest_day: bool
    source_plan_id: Optional[uuid.UUID]
    created_at: datetime
    exercises: List[ScheduledExerciseResponse]

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/schemas/schedule.py
git commit -m "feat: add schedule pydantic schemas"
```

---

### Task 5: Plan CRUD — update create_plan, add PUT and DELETE (TDD)

**Files:**
- Modify: `backend/app/api/v1/plans.py`
- Create: `backend/tests/test_plans.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_plans.py`:

```python
"""
Tests for plan CRUD endpoints.
Pattern: override get_db + get_current_user; no real DB.
"""

import uuid
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_db, get_current_user
from app.models.plan import Exercise, Workout, WorkoutPlan
from app.models.user import UserRole
from tests.conftest import coach_user, make_mock_db


def _make_mock_plan(coach_id: uuid.UUID) -> WorkoutPlan:
    """Build a minimal mock WorkoutPlan for test assertions."""
    plan = WorkoutPlan()
    plan.id = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
    plan.coach_id = coach_id
    plan.title = "Test Plan"
    plan.description = None
    plan.created_at = datetime(2026, 1, 1)
    plan.workouts = []
    plan.assignments = []
    return plan


@pytest.fixture
def http_as_coach_with_plan(coach_user):
    mock_plan = _make_mock_plan(coach_user.id)
    mock_db = make_mock_db(return_value=mock_plan)

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: coach_user
    yield TestClient(app), mock_db, mock_plan
    app.dependency_overrides.clear()


@pytest.fixture
def http_as_coach_no_plan(coach_user):
    mock_db = make_mock_db(return_value=None)

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: coach_user
    yield TestClient(app), mock_db
    app.dependency_overrides.clear()


@pytest.fixture
def http_as_coach_create(coach_user):
    """
    For create_plan: execute() is called twice — once to flush (no-op) and once
    to reload. We simulate both by making scalar_one() return the mock plan.
    """
    mock_plan = _make_mock_plan(coach_user.id)
    mock_db = AsyncMock()
    result = MagicMock()
    result.scalar_one.return_value = mock_plan
    result.scalar_one_or_none.return_value = mock_plan
    mock_db.execute.return_value = result
    mock_db.commit = AsyncMock()
    mock_db.flush = AsyncMock()
    mock_db.add = MagicMock()

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: coach_user
    yield TestClient(app), mock_db, mock_plan
    app.dependency_overrides.clear()


# --- Create plan ---

def test_create_plan_returns_201(http_as_coach_create):
    client, mock_db, mock_plan = http_as_coach_create
    response = client.post(
        "/api/v1/plans/",
        json={
            "title": "Summer Shred",
            "description": "6-week cut",
            "workouts": [
                {
                    "title": "Upper Body",
                    "order": 1,
                    "is_rest_day": False,
                    "exercises": [
                        {"label": "A", "name": "Bench Press", "description": "5x5 @ 75%", "order": 1}
                    ],
                }
            ],
        },
    )
    assert response.status_code == 201


def test_create_plan_rest_day_no_exercises(http_as_coach_create):
    client, mock_db, mock_plan = http_as_coach_create
    response = client.post(
        "/api/v1/plans/",
        json={
            "title": "Plan with Rest",
            "workouts": [
                {"order": 1, "is_rest_day": True},
            ],
        },
    )
    assert response.status_code == 201


# --- Update plan ---

def test_update_plan_returns_200(http_as_coach_with_plan):
    client, mock_db, mock_plan = http_as_coach_with_plan
    mock_plan.workouts = []
    response = client.put(
        f"/api/v1/plans/{mock_plan.id}",
        json={"title": "Updated Title", "workouts": []},
    )
    assert response.status_code == 200


def test_update_plan_not_found_returns_404(http_as_coach_no_plan):
    client, mock_db = http_as_coach_no_plan
    response = client.put(
        f"/api/v1/plans/{uuid.uuid4()}",
        json={"title": "x", "workouts": []},
    )
    assert response.status_code == 404


# --- Delete plan ---

def test_delete_plan_returns_204(http_as_coach_with_plan):
    client, mock_db, mock_plan = http_as_coach_with_plan
    response = client.delete(f"/api/v1/plans/{mock_plan.id}")
    assert response.status_code == 204


def test_delete_plan_not_found_returns_404(http_as_coach_no_plan):
    client, mock_db = http_as_coach_no_plan
    response = client.delete(f"/api/v1/plans/{uuid.uuid4()}")
    assert response.status_code == 404
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && source /d/CodingProjects/ProgramPigeon/backend/venv/Scripts/activate && python -m pytest tests/test_plans.py -v
```

Expected: FAILED — `create_plan` uses old exercise fields; `PUT`/`DELETE` routes don't exist yet.

- [ ] **Step 3: Update `create_plan` in `plans.py`**

Replace the `create_plan` handler body (keep the decorator and signature):

```python
@router.post("/", response_model=WorkoutPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    data: WorkoutPlanCreate,
    db: AsyncSession = Depends(get_db),
    coach: User = Depends(require_coach),
):
    """
    Create a new workout plan with nested workouts and exercise blocks.
    Only accessible by coaches. The plan is owned by the authenticated coach.
    """
    plan = WorkoutPlan(coach_id=coach.id, title=data.title, description=data.description)
    db.add(plan)
    await db.flush()

    for workout_data in data.workouts:
        workout = Workout(
            plan_id=plan.id,
            title=workout_data.title,
            order=workout_data.order,
            notes=workout_data.notes,
            is_rest_day=workout_data.is_rest_day,
        )
        db.add(workout)
        await db.flush()

        if not workout_data.is_rest_day:
            for exercise_data in workout_data.exercises:
                db.add(Exercise(
                    workout_id=workout.id,
                    label=exercise_data.label,
                    name=exercise_data.name,
                    description=exercise_data.description,
                    order=exercise_data.order,
                ))

    await db.commit()

    result = await db.execute(
        select(WorkoutPlan)
        .where(WorkoutPlan.id == plan.id)
        .options(selectinload(WorkoutPlan.workouts).selectinload(Workout.exercises))
    )
    return result.scalar_one()
```

- [ ] **Step 4: Add `PUT /{plan_id}` to `plans.py`**

```python
@router.put("/{plan_id}", response_model=WorkoutPlanResponse)
async def update_plan(
    plan_id: uuid.UUID,
    data: WorkoutPlanCreate,
    db: AsyncSession = Depends(get_db),
    coach: User = Depends(require_coach),
):
    """
    Replace a workout plan's workouts and exercise blocks wholesale.
    Only the owning coach can update the plan.
    """
    result = await db.execute(
        select(WorkoutPlan)
        .where(WorkoutPlan.id == plan_id, WorkoutPlan.coach_id == coach.id)
        .options(selectinload(WorkoutPlan.workouts).selectinload(Workout.exercises))
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    plan.title = data.title
    plan.description = data.description

    for workout in plan.workouts:
        await db.delete(workout)
    await db.flush()

    for workout_data in data.workouts:
        workout = Workout(
            plan_id=plan.id,
            title=workout_data.title,
            order=workout_data.order,
            notes=workout_data.notes,
            is_rest_day=workout_data.is_rest_day,
        )
        db.add(workout)
        await db.flush()

        if not workout_data.is_rest_day:
            for exercise_data in workout_data.exercises:
                db.add(Exercise(
                    workout_id=workout.id,
                    label=exercise_data.label,
                    name=exercise_data.name,
                    description=exercise_data.description,
                    order=exercise_data.order,
                ))

    await db.commit()

    result = await db.execute(
        select(WorkoutPlan)
        .where(WorkoutPlan.id == plan_id)
        .options(selectinload(WorkoutPlan.workouts).selectinload(Workout.exercises))
    )
    return result.scalar_one()
```

- [ ] **Step 5: Add `DELETE /{plan_id}` to `plans.py`**

```python
@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    coach: User = Depends(require_coach),
):
    """
    Delete a workout plan and all its workouts and exercise blocks.
    Only the owning coach can delete the plan.
    """
    result = await db.execute(
        select(WorkoutPlan).where(WorkoutPlan.id == plan_id, WorkoutPlan.coach_id == coach.id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    await db.delete(plan)
    await db.commit()
```

- [ ] **Step 6: Run tests — verify they pass**

```bash
python -m pytest tests/test_plans.py -v
```

Expected: 7 passed.

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/v1/plans.py backend/tests/test_plans.py
git commit -m "feat: update create_plan for new exercise model; add PUT and DELETE plan routes"
```

---

### Task 6: Schedule service + updated assign endpoint (TDD)

**Files:**
- Create: `backend/app/services/schedule.py`
- Modify: `backend/app/api/v1/plans.py`

- [ ] **Step 1: Write failing tests for assign endpoint**

Add to `backend/tests/test_plans.py`:

```python
# --- Assign plan ---

@pytest.fixture
def http_as_coach_assign(coach_user):
    """
    assign_plan calls execute() multiple times:
    1. To find the plan (scalar_one_or_none → mock_plan)
    2. To check for duplicate assignment (scalar_one_or_none → None = no duplicate)
    3. Inside instantiate_plan_for_client (flush calls)
    Use side_effect to sequence the return values.
    """
    mock_plan = _make_mock_plan(coach_user.id)
    mock_plan.workouts = []  # empty plan, no workouts to instantiate

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    plan_result = MagicMock()
    plan_result.scalar_one_or_none.return_value = mock_plan

    no_dup_result = MagicMock()
    no_dup_result.scalar_one_or_none.return_value = None

    assignment_result = MagicMock()
    mock_assignment = MagicMock()
    mock_assignment.id = uuid.uuid4()
    mock_assignment.plan_id = mock_plan.id
    mock_assignment.client_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    mock_assignment.start_date = "2026-05-01"
    mock_assignment.assigned_at = datetime(2026, 5, 1)
    assignment_result.scalar_one_or_none.return_value = mock_assignment

    mock_db.execute.side_effect = [plan_result, no_dup_result]

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: coach_user
    yield TestClient(app), mock_db
    app.dependency_overrides.clear()


def test_assign_plan_requires_start_date(http_as_coach_assign):
    client, mock_db = http_as_coach_assign
    plan_id = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
    response = client.post(
        f"/api/v1/plans/{plan_id}/assign",
        json={"client_id": "00000000-0000-0000-0000-000000000002"},  # missing start_date
    )
    assert response.status_code == 422


def test_assign_plan_with_start_date_returns_201(http_as_coach_assign):
    client, mock_db = http_as_coach_assign
    plan_id = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
    response = client.post(
        f"/api/v1/plans/{plan_id}/assign",
        json={
            "client_id": "00000000-0000-0000-0000-000000000002",
            "start_date": "2026-05-01",
        },
    )
    assert response.status_code == 201
```

- [ ] **Step 2: Run new tests — verify they fail**

```bash
python -m pytest tests/test_plans.py::test_assign_plan_requires_start_date tests/test_plans.py::test_assign_plan_with_start_date_returns_201 -v
```

Expected: FAILED — `start_date` not in schema yet / 422 test might pass but 201 test fails.

- [ ] **Step 3: Create the schedule service**

Create `backend/app/services/schedule.py`:

```python
"""
Business logic for instantiating a WorkoutPlan onto a client's schedule.
Called when a coach assigns a plan to a client.
"""

import uuid
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plan import ScheduledExercise, ScheduledWorkout, WorkoutPlan


async def instantiate_plan_for_client(
    db: AsyncSession,
    plan: WorkoutPlan,
    client_id: uuid.UUID,
    coach_id: uuid.UUID,
    start_date: date,
) -> None:
    """
    Copy every workout from `plan` onto the client's calendar starting from `start_date`.
    Each workout (including rest days) occupies one consecutive calendar day.
    Exercise blocks are copied into ScheduledExercise rows.
    The resulting ScheduledWorkout rows are independent of the plan template.

    Args:
        db: Active async DB session (caller must commit after this returns).
        plan: The WorkoutPlan to instantiate. Must have `workouts` and their
              `exercises` eagerly loaded before calling.
        client_id: UUID of the client receiving the schedule.
        coach_id: UUID of the coach assigning the plan.
        start_date: The calendar date for the first workout in the plan.
    """
    for i, workout in enumerate(sorted(plan.workouts, key=lambda w: w.order)):
        scheduled_date = start_date + timedelta(days=i)
        scheduled_workout = ScheduledWorkout(
            client_id=client_id,
            coach_id=coach_id,
            date=scheduled_date,
            title=workout.title,
            notes=workout.notes,
            is_rest_day=workout.is_rest_day,
            source_plan_id=plan.id,
        )
        db.add(scheduled_workout)
        await db.flush()

        if not workout.is_rest_day:
            for exercise in sorted(workout.exercises, key=lambda e: e.order):
                db.add(ScheduledExercise(
                    scheduled_workout_id=scheduled_workout.id,
                    label=exercise.label,
                    name=exercise.name,
                    description=exercise.description,
                    order=exercise.order,
                ))
```

- [ ] **Step 4: Update `assign_plan` in `plans.py`**

Replace the `assign_plan` handler. Add to imports at top: `from app.services.schedule import instantiate_plan_for_client` and `from datetime import date`.

```python
@router.post("/{plan_id}/assign", response_model=PlanAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_plan(
    plan_id: uuid.UUID,
    data: PlanAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    coach: User = Depends(require_coach),
):
    """
    Assign a workout plan to a client and populate their calendar.
    Workouts are copied onto consecutive dates starting from `data.start_date`.
    The authenticated coach must own the plan.
    """
    result = await db.execute(
        select(WorkoutPlan)
        .where(WorkoutPlan.id == plan_id, WorkoutPlan.coach_id == coach.id)
        .options(selectinload(WorkoutPlan.workouts).selectinload(Workout.exercises))
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    existing = await db.execute(
        select(PlanAssignment).where(
            PlanAssignment.plan_id == plan_id,
            PlanAssignment.client_id == data.client_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plan already assigned to this client")

    assignment = PlanAssignment(
        plan_id=plan_id,
        client_id=data.client_id,
        start_date=data.start_date,
    )
    db.add(assignment)
    await db.flush()

    await instantiate_plan_for_client(
        db,
        plan=plan,
        client_id=data.client_id,
        coach_id=coach.id,
        start_date=data.start_date,
    )

    await db.commit()
    await db.refresh(assignment)
    return assignment
```

- [ ] **Step 5: Run all plan tests**

```bash
python -m pytest tests/test_plans.py -v
```

Expected: 9 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/schedule.py backend/app/api/v1/plans.py backend/tests/test_plans.py
git commit -m "feat: add schedule service; update assign_plan to accept start_date and instantiate schedule"
```

---

### Task 7: Client schedule CRUD routes (TDD)

**Files:**
- Create: `backend/app/api/v1/schedule.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_schedule.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_schedule.py`:

```python
"""
Tests for client schedule endpoints.
"""

import uuid
import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_db, get_current_user
from app.models.plan import ScheduledExercise, ScheduledWorkout
from tests.conftest import coach_user, client_user, make_mock_db

CLIENT_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
WORKOUT_ID = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000001")


def _make_mock_scheduled_workout() -> ScheduledWorkout:
    sw = ScheduledWorkout()
    sw.id = WORKOUT_ID
    sw.client_id = CLIENT_ID
    sw.coach_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    sw.date = date(2026, 5, 1)
    sw.title = "Upper Body"
    sw.notes = None
    sw.is_rest_day = False
    sw.source_plan_id = None
    sw.created_at = datetime(2026, 5, 1)
    sw.exercises = []
    return sw


def _make_coach_db_with_access(return_value):
    """
    Mock DB where the first execute (coach_client check) returns a row,
    and the second execute returns the given value.
    """
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.delete = AsyncMock()

    access_result = MagicMock()
    access_result.first.return_value = ("row",)  # truthy = has access

    main_result = MagicMock()
    main_result.scalar_one_or_none.return_value = return_value
    main_result.scalars.return_value.all.return_value = [return_value] if return_value else []
    main_result.scalar_one.return_value = return_value

    mock_db.execute.side_effect = [access_result, main_result, main_result]
    return mock_db


@pytest.fixture
def http_coach_with_workout(coach_user):
    mock_sw = _make_mock_scheduled_workout()
    mock_db = _make_coach_db_with_access(mock_sw)

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: coach_user
    yield TestClient(app), mock_db
    app.dependency_overrides.clear()


@pytest.fixture
def http_coach_no_workout(coach_user):
    mock_db = _make_coach_db_with_access(None)

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: coach_user
    yield TestClient(app), mock_db
    app.dependency_overrides.clear()


@pytest.fixture
def http_client_own_schedule(client_user):
    """Client reading their own schedule — no coach_client check needed."""
    mock_sw = _make_mock_scheduled_workout()
    mock_db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = [mock_sw]
    mock_db.execute.return_value = result

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: client_user
    yield TestClient(app)
    app.dependency_overrides.clear()


# --- GET schedule ---

def test_get_schedule_returns_list(http_coach_with_workout):
    client, _ = http_coach_with_workout
    response = client.get(
        f"/api/v1/clients/{CLIENT_ID}/schedule",
        params={"start": "2026-05-01", "end": "2026-05-31"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_client_can_read_own_schedule(http_client_own_schedule):
    response = http_client_own_schedule.get(
        f"/api/v1/clients/{CLIENT_ID}/schedule",
        params={"start": "2026-05-01", "end": "2026-05-31"},
    )
    assert response.status_code == 200


# --- POST schedule ---

def test_create_scheduled_workout_returns_201(http_coach_with_workout):
    client, _ = http_coach_with_workout
    response = client.post(
        f"/api/v1/clients/{CLIENT_ID}/schedule",
        json={
            "date": "2026-05-10",
            "title": "Leg Day",
            "is_rest_day": False,
            "exercises": [
                {"label": "A", "name": "Squat", "description": "5x5", "order": 1}
            ],
        },
    )
    assert response.status_code == 201


def test_create_rest_day_returns_201(http_coach_with_workout):
    client, _ = http_coach_with_workout
    response = client.post(
        f"/api/v1/clients/{CLIENT_ID}/schedule",
        json={"date": "2026-05-11", "is_rest_day": True},
    )
    assert response.status_code == 201


# --- PUT schedule ---

def test_update_scheduled_workout_returns_200(http_coach_with_workout):
    client, _ = http_coach_with_workout
    response = client.put(
        f"/api/v1/clients/{CLIENT_ID}/schedule/{WORKOUT_ID}",
        json={"title": "Updated", "is_rest_day": False, "exercises": []},
    )
    assert response.status_code == 200


def test_update_nonexistent_workout_returns_404(http_coach_no_workout):
    client, _ = http_coach_no_workout
    response = client.put(
        f"/api/v1/clients/{CLIENT_ID}/schedule/{uuid.uuid4()}",
        json={"title": "x", "is_rest_day": False, "exercises": []},
    )
    assert response.status_code == 404


# --- DELETE schedule ---

def test_delete_scheduled_workout_returns_204(http_coach_with_workout):
    client, _ = http_coach_with_workout
    response = client.delete(f"/api/v1/clients/{CLIENT_ID}/schedule/{WORKOUT_ID}")
    assert response.status_code == 204


def test_delete_nonexistent_workout_returns_404(http_coach_no_workout):
    client, _ = http_coach_no_workout
    response = client.delete(f"/api/v1/clients/{CLIENT_ID}/schedule/{uuid.uuid4()}")
    assert response.status_code == 404
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
python -m pytest tests/test_schedule.py -v
```

Expected: FAILED — 404 on all routes (router not registered yet).

- [ ] **Step 3: Create `backend/app/api/v1/schedule.py`**

```python
"""
Client schedule routes: CRUD for per-client scheduled workouts.
Coaches create and manage; clients can read their own schedule.
"""

import uuid
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db, require_coach
from app.models.plan import ScheduledExercise, ScheduledWorkout
from app.models.user import User, coach_client
from app.schemas.schedule import (
    ScheduledWorkoutCreate,
    ScheduledWorkoutResponse,
    ScheduledWorkoutUpdate,
)

router = APIRouter()


async def _require_coach_client_access(db: AsyncSession, coach_id: uuid.UUID, client_id: uuid.UUID) -> None:
    """Raise 404 if the coach does not own this client relationship."""
    result = await db.execute(
        select(coach_client).where(
            coach_client.c.coach_id == coach_id,
            coach_client.c.client_id == client_id,
        )
    )
    if not result.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")


@router.get("/{client_id}/schedule", response_model=List[ScheduledWorkoutResponse])
async def get_schedule(
    client_id: uuid.UUID,
    start: date = Query(...),
    end: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return all scheduled workouts (including rest days) for a client within a date range.
    Coaches must own the client relationship. Clients can read their own schedule.
    """
    if current_user.role.value == "coach":
        await _require_coach_client_access(db, current_user.id, client_id)
    elif current_user.id != client_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    result = await db.execute(
        select(ScheduledWorkout)
        .where(
            ScheduledWorkout.client_id == client_id,
            ScheduledWorkout.date >= start,
            ScheduledWorkout.date <= end,
        )
        .options(selectinload(ScheduledWorkout.exercises))
        .order_by(ScheduledWorkout.date)
    )
    return result.scalars().all()


@router.post("/{client_id}/schedule", response_model=ScheduledWorkoutResponse, status_code=status.HTTP_201_CREATED)
async def create_scheduled_workout(
    client_id: uuid.UUID,
    data: ScheduledWorkoutCreate,
    db: AsyncSession = Depends(get_db),
    coach: User = Depends(require_coach),
):
    """Create a one-off scheduled workout on a client's calendar."""
    await _require_coach_client_access(db, coach.id, client_id)

    sw = ScheduledWorkout(
        client_id=client_id,
        coach_id=coach.id,
        date=data.date,
        title=data.title,
        notes=data.notes,
        is_rest_day=data.is_rest_day,
    )
    db.add(sw)
    await db.flush()

    if not data.is_rest_day:
        for ex in data.exercises:
            db.add(ScheduledExercise(
                scheduled_workout_id=sw.id,
                label=ex.label,
                name=ex.name,
                description=ex.description,
                order=ex.order,
            ))

    await db.commit()

    result = await db.execute(
        select(ScheduledWorkout)
        .where(ScheduledWorkout.id == sw.id)
        .options(selectinload(ScheduledWorkout.exercises))
    )
    return result.scalar_one()


@router.get("/{client_id}/schedule/{workout_id}", response_model=ScheduledWorkoutResponse)
async def get_scheduled_workout(
    client_id: uuid.UUID,
    workout_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a single scheduled workout by ID."""
    if current_user.role.value == "coach":
        await _require_coach_client_access(db, current_user.id, client_id)
    elif current_user.id != client_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    result = await db.execute(
        select(ScheduledWorkout)
        .where(ScheduledWorkout.id == workout_id, ScheduledWorkout.client_id == client_id)
        .options(selectinload(ScheduledWorkout.exercises))
    )
    sw = result.scalar_one_or_none()
    if not sw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled workout not found")
    return sw


@router.put("/{client_id}/schedule/{workout_id}", response_model=ScheduledWorkoutResponse)
async def update_scheduled_workout(
    client_id: uuid.UUID,
    workout_id: uuid.UUID,
    data: ScheduledWorkoutUpdate,
    db: AsyncSession = Depends(get_db),
    coach: User = Depends(require_coach),
):
    """Replace a scheduled workout's exercise blocks wholesale."""
    await _require_coach_client_access(db, coach.id, client_id)

    result = await db.execute(
        select(ScheduledWorkout)
        .where(ScheduledWorkout.id == workout_id, ScheduledWorkout.client_id == client_id)
        .options(selectinload(ScheduledWorkout.exercises))
    )
    sw = result.scalar_one_or_none()
    if not sw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled workout not found")

    sw.title = data.title
    sw.notes = data.notes
    sw.is_rest_day = data.is_rest_day

    for ex in sw.exercises:
        await db.delete(ex)
    await db.flush()

    if not data.is_rest_day:
        for ex in data.exercises:
            db.add(ScheduledExercise(
                scheduled_workout_id=sw.id,
                label=ex.label,
                name=ex.name,
                description=ex.description,
                order=ex.order,
            ))

    await db.commit()

    result = await db.execute(
        select(ScheduledWorkout)
        .where(ScheduledWorkout.id == workout_id)
        .options(selectinload(ScheduledWorkout.exercises))
    )
    return result.scalar_one()


@router.delete("/{client_id}/schedule/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_workout(
    client_id: uuid.UUID,
    workout_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    coach: User = Depends(require_coach),
):
    """Delete a scheduled workout and its exercise blocks."""
    await _require_coach_client_access(db, coach.id, client_id)

    result = await db.execute(
        select(ScheduledWorkout).where(
            ScheduledWorkout.id == workout_id,
            ScheduledWorkout.client_id == client_id,
        )
    )
    sw = result.scalar_one_or_none()
    if not sw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled workout not found")

    await db.delete(sw)
    await db.commit()
```

- [ ] **Step 4: Register the schedule router in `main.py`**

```python
# Add to imports:
from app.api.v1 import auth, users, plans, messages, schedule

# Add after existing include_router calls:
app.include_router(schedule.router, prefix="/api/v1/clients", tags=["schedule"])
```

- [ ] **Step 5: Run all tests**

```bash
python -m pytest tests/ -v
```

Expected: all tests pass (test_health, test_auth, test_users, test_plans, test_schedule).

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/v1/schedule.py backend/app/main.py backend/tests/test_schedule.py
git commit -m "feat: add client schedule CRUD routes and register router"
```

---

### Task 8: Frontend — update types and API functions

**Files:**
- Modify: `frontend/src/types/plan.ts`
- Create: `frontend/src/types/schedule.ts`
- Modify: `frontend/src/api/plans.ts`
- Create: `frontend/src/api/schedule.ts`

- [ ] **Step 1: Update `frontend/src/types/plan.ts`**

```typescript
/** A single exercise block within a workout. */
export interface Exercise {
  id: string
  workout_id: string
  label: string
  name: string
  description: string | null
  order: number
}

/** A single workout session within a plan. */
export interface Workout {
  id: string
  plan_id: string
  title: string | null
  order: number
  notes: string | null
  is_rest_day: boolean
  exercises: Exercise[]
}

/** A full workout plan with nested workouts. */
export interface WorkoutPlan {
  id: string
  coach_id: string
  title: string
  description: string | null
  created_at: string
  workouts: Workout[]
}

/** Confirmation that a plan was assigned to a client. */
export interface PlanAssignment {
  id: string
  plan_id: string
  client_id: string
  start_date: string
  assigned_at: string
}

/** Request body for creating an exercise block. */
export interface ExercisePayload {
  label: string
  name: string
  description?: string
  order: number
}

/** Request body for creating a workout. */
export interface WorkoutPayload {
  title?: string
  order: number
  notes?: string
  is_rest_day?: boolean
  exercises: ExercisePayload[]
}

/** Request body for creating a workout plan. */
export interface CreatePlanPayload {
  title: string
  description?: string
  workouts: WorkoutPayload[]
}
```

- [ ] **Step 2: Create `frontend/src/types/schedule.ts`**

```typescript
/** A scheduled exercise block on a client's calendar. */
export interface ScheduledExercise {
  id: string
  scheduled_workout_id: string
  label: string
  name: string
  description: string | null
  order: number
}

/** A scheduled workout on a client's calendar. */
export interface ScheduledWorkout {
  id: string
  client_id: string
  coach_id: string
  date: string
  title: string | null
  notes: string | null
  is_rest_day: boolean
  source_plan_id: string | null
  created_at: string
  exercises: ScheduledExercise[]
}

export interface ScheduledExercisePayload {
  label: string
  name: string
  description?: string
  order: number
}

export interface CreateScheduledWorkoutPayload {
  date: string
  title?: string
  notes?: string
  is_rest_day?: boolean
  exercises: ScheduledExercisePayload[]
}

export interface UpdateScheduledWorkoutPayload {
  title?: string
  notes?: string
  is_rest_day?: boolean
  exercises: ScheduledExercisePayload[]
}
```

- [ ] **Step 3: Update `frontend/src/api/plans.ts`**

```typescript
/**
 * Workout plan API functions: create, fetch, update, delete, and assign plans.
 */

import apiClient from './client'
import type { CreatePlanPayload, PlanAssignment, WorkoutPlan } from '@/types/plan'

export async function getPlans(): Promise<WorkoutPlan[]> {
  const { data } = await apiClient.get<WorkoutPlan[]>('/plans')
  return data
}

export async function getPlan(planId: string): Promise<WorkoutPlan> {
  const { data } = await apiClient.get<WorkoutPlan>(`/plans/${planId}`)
  return data
}

export async function createPlan(payload: CreatePlanPayload): Promise<WorkoutPlan> {
  const { data } = await apiClient.post<WorkoutPlan>('/plans', payload)
  return data
}

export async function updatePlan(planId: string, payload: CreatePlanPayload): Promise<WorkoutPlan> {
  const { data } = await apiClient.put<WorkoutPlan>(`/plans/${planId}`, payload)
  return data
}

export async function deletePlan(planId: string): Promise<void> {
  await apiClient.delete(`/plans/${planId}`)
}

export async function assignPlan(
  planId: string,
  clientId: string,
  startDate: string,
): Promise<PlanAssignment> {
  const { data } = await apiClient.post<PlanAssignment>(`/plans/${planId}/assign`, {
    client_id: clientId,
    start_date: startDate,
  })
  return data
}
```

- [ ] **Step 4: Create `frontend/src/api/schedule.ts`**

```typescript
/**
 * Client schedule API functions.
 */

import apiClient from './client'
import type {
  CreateScheduledWorkoutPayload,
  ScheduledWorkout,
  UpdateScheduledWorkoutPayload,
} from '@/types/schedule'

export async function getSchedule(
  clientId: string,
  start: string,
  end: string,
): Promise<ScheduledWorkout[]> {
  const { data } = await apiClient.get<ScheduledWorkout[]>(
    `/clients/${clientId}/schedule`,
    { params: { start, end } },
  )
  return data
}

export async function createScheduledWorkout(
  clientId: string,
  payload: CreateScheduledWorkoutPayload,
): Promise<ScheduledWorkout> {
  const { data } = await apiClient.post<ScheduledWorkout>(
    `/clients/${clientId}/schedule`,
    payload,
  )
  return data
}

export async function updateScheduledWorkout(
  clientId: string,
  workoutId: string,
  payload: UpdateScheduledWorkoutPayload,
): Promise<ScheduledWorkout> {
  const { data } = await apiClient.put<ScheduledWorkout>(
    `/clients/${clientId}/schedule/${workoutId}`,
    payload,
  )
  return data
}

export async function deleteScheduledWorkout(
  clientId: string,
  workoutId: string,
): Promise<void> {
  await apiClient.delete(`/clients/${clientId}/schedule/${workoutId}`)
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/types/plan.ts frontend/src/types/schedule.ts frontend/src/api/plans.ts frontend/src/api/schedule.ts
git commit -m "feat: update plan types and API; add schedule types and API"
```

---

### Task 9: PlanBuilderForm component

**Files:**
- Create: `frontend/src/components/PlanBuilderForm.tsx`
- Create: `frontend/src/components/PlanBuilderForm.module.css`

- [ ] **Step 1: Create `PlanBuilderForm.tsx`**

```tsx
/**
 * PlanBuilderForm: shared form for creating and editing workout plans.
 * Manages plan title, description, and an ordered list of workout days.
 * Each day has a title, optional notes, a rest day toggle, and exercise blocks.
 */

import { useState } from 'react'
import type { CreatePlanPayload, ExercisePayload, WorkoutPayload } from '@/types/plan'
import styles from './PlanBuilderForm.module.css'

type ExerciseForm = { _id: string; label: string; name: string; description: string }
type DayForm = { _id: string; title: string; notes: string; isRestDay: boolean; exercises: ExerciseForm[] }

function newExercise(): ExerciseForm {
  return { _id: crypto.randomUUID(), label: '', name: '', description: '' }
}

function newDay(): DayForm {
  return { _id: crypto.randomUUID(), title: '', notes: '', isRestDay: false, exercises: [newExercise()] }
}

function toPayload(title: string, description: string, days: DayForm[]): CreatePlanPayload {
  return {
    title,
    description: description || undefined,
    workouts: days.map((day, i) => ({
      title: day.title || undefined,
      order: i + 1,
      notes: day.notes || undefined,
      is_rest_day: day.isRestDay,
      exercises: day.isRestDay
        ? []
        : day.exercises.map((ex, j) => ({
            label: ex.label,
            name: ex.name,
            description: ex.description || undefined,
            order: j + 1,
          })),
    })),
  }
}

interface Props {
  initialTitle?: string
  initialDescription?: string
  initialDays?: DayForm[]
  onSave: (payload: CreatePlanPayload) => Promise<void>
  saving: boolean
  saveLabel?: string
}

export type { DayForm, ExerciseForm }

export default function PlanBuilderForm({
  initialTitle = '',
  initialDescription = '',
  initialDays,
  onSave,
  saving,
  saveLabel = 'Save Plan',
}: Props) {
  const [title, setTitle] = useState(initialTitle)
  const [description, setDescription] = useState(initialDescription)
  const [days, setDays] = useState<DayForm[]>(initialDays ?? [newDay()])
  const [error, setError] = useState<string | null>(null)

  function updateDay(id: string, patch: Partial<DayForm>) {
    setDays(ds => ds.map(d => (d._id === id ? { ...d, ...patch } : d)))
  }

  function updateExercise(dayId: string, exId: string, patch: Partial<ExerciseForm>) {
    setDays(ds =>
      ds.map(d =>
        d._id === dayId
          ? { ...d, exercises: d.exercises.map(ex => (ex._id === exId ? { ...ex, ...patch } : ex)) }
          : d,
      ),
    )
  }

  function addExercise(dayId: string) {
    setDays(ds =>
      ds.map(d => (d._id === dayId ? { ...d, exercises: [...d.exercises, newExercise()] } : d)),
    )
  }

  function removeExercise(dayId: string, exId: string) {
    setDays(ds =>
      ds.map(d =>
        d._id === dayId ? { ...d, exercises: d.exercises.filter(ex => ex._id !== exId) } : d,
      ),
    )
  }

  function addDay() {
    setDays(ds => [...ds, newDay()])
  }

  function removeDay(id: string) {
    setDays(ds => ds.filter(d => d._id !== id))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!title.trim()) { setError('Plan title is required.'); return }
    setError(null)
    await onSave(toPayload(title, description, days))
  }

  return (
    <form onSubmit={handleSubmit} className={styles.form}>
      <div className={styles.planMeta}>
        <input
          className={styles.planTitle}
          placeholder="Plan title"
          value={title}
          onChange={e => setTitle(e.target.value)}
          required
        />
        <textarea
          className={styles.planDescription}
          placeholder="Description (optional)"
          value={description}
          onChange={e => setDescription(e.target.value)}
          rows={2}
        />
      </div>

      {days.map((day, dayIdx) => (
        <div key={day._id} className={styles.day}>
          <div className={styles.dayHeader}>
            <span className={styles.dayLabel}>Day {dayIdx + 1}</span>
            <input
              className={styles.dayTitle}
              placeholder={day.isRestDay ? 'Rest Day' : 'Workout title (e.g. Upper Body)'}
              value={day.title}
              onChange={e => updateDay(day._id, { title: e.target.value })}
              disabled={day.isRestDay}
            />
            <label className={styles.restToggle}>
              <input
                type="checkbox"
                checked={day.isRestDay}
                onChange={e => updateDay(day._id, { isRestDay: e.target.checked })}
              />
              Rest day
            </label>
            {days.length > 1 && (
              <button type="button" className={styles.removeBtn} onClick={() => removeDay(day._id)}>
                ✕
              </button>
            )}
          </div>

          {!day.isRestDay && (
            <>
              <textarea
                className={styles.dayNotes}
                placeholder="Day notes (optional)"
                value={day.notes}
                onChange={e => updateDay(day._id, { notes: e.target.value })}
                rows={2}
              />
              <div className={styles.exercises}>
                {day.exercises.map(ex => (
                  <div key={ex._id} className={styles.exercise}>
                    <input
                      className={styles.exLabel}
                      placeholder="A"
                      value={ex.label}
                      onChange={e => updateExercise(day._id, ex._id, { label: e.target.value })}
                    />
                    <input
                      className={styles.exName}
                      placeholder="Exercise name"
                      value={ex.name}
                      onChange={e => updateExercise(day._id, ex._id, { name: e.target.value })}
                    />
                    <textarea
                      className={styles.exDescription}
                      placeholder="Sets, reps, tempo, notes..."
                      value={ex.description}
                      onChange={e => updateExercise(day._id, ex._id, { description: e.target.value })}
                      rows={2}
                    />
                    {day.exercises.length > 1 && (
                      <button
                        type="button"
                        className={styles.removeBtn}
                        onClick={() => removeExercise(day._id, ex._id)}
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))}
                <button type="button" className={styles.addExercise} onClick={() => addExercise(day._id)}>
                  + Add Exercise Block
                </button>
              </div>
            </>
          )}
        </div>
      ))}

      <button type="button" className={styles.addDay} onClick={addDay}>
        + Add Day
      </button>

      {error && <p className={styles.error}>{error}</p>}

      <button type="submit" className={styles.saveBtn} disabled={saving}>
        {saving ? 'Saving...' : saveLabel}
      </button>
    </form>
  )
}
```

- [ ] **Step 2: Create `PlanBuilderForm.module.css`**

```css
.form { display: flex; flex-direction: column; gap: 20px; }

.planMeta { display: flex; flex-direction: column; gap: 8px; }

.planTitle {
  font-size: 1.4rem;
  font-weight: 700;
  background: transparent;
  border: none;
  border-bottom: 2px solid #333;
  color: #fff;
  padding: 6px 0;
  outline: none;
  width: 100%;
}
.planTitle:focus { border-bottom-color: #f97316; }

.planDescription, .dayNotes, .exDescription {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 6px;
  color: #ccc;
  padding: 8px;
  resize: vertical;
  font-size: 0.9rem;
  width: 100%;
  box-sizing: border-box;
}
.planDescription:focus, .dayNotes:focus, .exDescription:focus { border-color: #f97316; outline: none; }

.day {
  background: #111;
  border: 1px solid #2a2a2a;
  border-radius: 10px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dayHeader { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

.dayLabel { color: #f97316; font-weight: 700; font-size: 0.85rem; white-space: nowrap; }

.dayTitle {
  flex: 1;
  background: transparent;
  border: none;
  border-bottom: 1px solid #333;
  color: #fff;
  padding: 4px 0;
  font-size: 1rem;
  outline: none;
}
.dayTitle:focus { border-bottom-color: #f97316; }
.dayTitle:disabled { color: #555; }

.restToggle { display: flex; align-items: center; gap: 6px; color: #888; font-size: 0.85rem; cursor: pointer; }
.restToggle input { accent-color: #f97316; }

.exercises { display: flex; flex-direction: column; gap: 8px; }

.exercise {
  display: grid;
  grid-template-columns: 48px 1fr;
  grid-template-rows: auto auto;
  gap: 6px;
  background: #1a1a1a;
  border-radius: 6px;
  padding: 10px;
  position: relative;
}

.exLabel {
  grid-row: 1;
  grid-column: 1;
  background: #222;
  border: 1px solid #333;
  border-radius: 4px;
  color: #f97316;
  font-weight: 700;
  text-align: center;
  padding: 4px;
  outline: none;
  font-size: 0.9rem;
}
.exLabel:focus { border-color: #f97316; }

.exName {
  grid-row: 1;
  grid-column: 2;
  background: transparent;
  border: none;
  border-bottom: 1px solid #333;
  color: #fff;
  padding: 4px 0;
  font-size: 0.95rem;
  outline: none;
}
.exName:focus { border-bottom-color: #f97316; }

.exDescription { grid-row: 2; grid-column: 1 / 3; }

.removeBtn {
  background: none;
  border: none;
  color: #555;
  cursor: pointer;
  font-size: 0.85rem;
  padding: 2px 6px;
}
.removeBtn:hover { color: #f87171; }

.addExercise, .addDay {
  background: none;
  border: 1px dashed #333;
  border-radius: 6px;
  color: #f97316;
  cursor: pointer;
  font-size: 0.85rem;
  padding: 8px;
  width: 100%;
  text-align: center;
}
.addExercise:hover, .addDay:hover { border-color: #f97316; background: #1a1a1a; }

.saveBtn {
  background: #f97316;
  border: none;
  border-radius: 8px;
  color: #000;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 700;
  padding: 12px;
  width: 100%;
}
.saveBtn:disabled { opacity: 0.5; cursor: not-allowed; }

.error { color: #f87171; font-size: 0.9rem; }
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/PlanBuilderForm.tsx frontend/src/components/PlanBuilderForm.module.css
git commit -m "feat: add PlanBuilderForm component"
```

---

### Task 10: CreatePlanPage and EditPlanPage

**Files:**
- Create: `frontend/src/pages/CreatePlanPage.tsx`
- Create: `frontend/src/pages/CreatePlanPage.module.css`
- Create: `frontend/src/pages/EditPlanPage.tsx`

- [ ] **Step 1: Create `CreatePlanPage.tsx`**

```tsx
/**
 * CreatePlanPage: coach creates a new workout plan.
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createPlan } from '@/api/plans'
import PlanBuilderForm from '@/components/PlanBuilderForm'
import type { CreatePlanPayload } from '@/types/plan'
import styles from './CreatePlanPage.module.css'

export default function CreatePlanPage() {
  const navigate = useNavigate()
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSave(payload: CreatePlanPayload) {
    setSaving(true)
    try {
      const plan = await createPlan(payload)
      navigate(`/plans/${plan.id}`)
    } catch {
      setError('Failed to save plan.')
      setSaving(false)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>New Plan</h1>
      </div>
      {error && <p className={styles.error}>{error}</p>}
      <PlanBuilderForm onSave={handleSave} saving={saving} saveLabel="Create Plan" />
    </div>
  )
}
```

- [ ] **Step 2: Create `CreatePlanPage.module.css`**

```css
.page { max-width: 800px; margin: 0 auto; padding: 32px 24px; }
.header { margin-bottom: 24px; }
.header h1 { font-size: 1.8rem; color: #fff; }
.error { color: #f87171; margin-bottom: 16px; }
```

- [ ] **Step 3: Create `EditPlanPage.tsx`**

```tsx
/**
 * EditPlanPage: pre-populates PlanBuilderForm with existing plan data.
 */

import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getPlan, updatePlan } from '@/api/plans'
import PlanBuilderForm from '@/components/PlanBuilderForm'
import type { CreatePlanPayload, WorkoutPlan } from '@/types/plan'
import type { DayForm, ExerciseForm } from '@/components/PlanBuilderForm'
import styles from './CreatePlanPage.module.css'

function planToDays(plan: WorkoutPlan): DayForm[] {
  return plan.workouts.map(w => ({
    _id: w.id,
    title: w.title ?? '',
    notes: w.notes ?? '',
    isRestDay: w.is_rest_day,
    exercises: w.exercises.map(ex => ({
      _id: ex.id,
      label: ex.label,
      name: ex.name,
      description: ex.description ?? '',
    })),
  }))
}

export default function EditPlanPage() {
  const { planId } = useParams<{ planId: string }>()
  const navigate = useNavigate()
  const [plan, setPlan] = useState<WorkoutPlan | null>(null)
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!planId) return
    getPlan(planId)
      .then(setPlan)
      .catch(() => setError('Plan not found.'))
      .finally(() => setLoading(false))
  }, [planId])

  async function handleSave(payload: CreatePlanPayload) {
    if (!planId) return
    setSaving(true)
    try {
      await updatePlan(planId, payload)
      navigate(`/plans/${planId}`)
    } catch {
      setError('Failed to update plan.')
      setSaving(false)
    }
  }

  if (loading) return <div className={styles.page}>Loading...</div>
  if (error || !plan) return <div className={styles.page}>{error ?? 'Plan not found.'}</div>

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>Edit Plan</h1>
      </div>
      <PlanBuilderForm
        initialTitle={plan.title}
        initialDescription={plan.description ?? ''}
        initialDays={planToDays(plan)}
        onSave={handleSave}
        saving={saving}
        saveLabel="Save Changes"
      />
    </div>
  )
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/CreatePlanPage.tsx frontend/src/pages/CreatePlanPage.module.css frontend/src/pages/EditPlanPage.tsx
git commit -m "feat: add CreatePlanPage and EditPlanPage"
```

---

### Task 11: Update PlanDetailPage

**Files:**
- Modify: `frontend/src/pages/PlanDetailPage.tsx`

- [ ] **Step 1: Replace `PlanDetailPage.tsx`**

```tsx
/**
 * PlanDetailPage: displays a single workout plan.
 * Coaches can edit, delete, or assign the plan to a client with a start date.
 */

import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getPlan, assignPlan, deletePlan } from '@/api/plans'
import { getClients } from '@/api/users'
import { useAuth } from '@/context/AuthContext'
import type { WorkoutPlan } from '@/types/plan'
import type { User } from '@/types/user'
import styles from './PlanDetailPage.module.css'

export default function PlanDetailPage() {
  const { planId } = useParams<{ planId: string }>()
  const { user } = useAuth()
  const navigate = useNavigate()
  const isCoach = user?.role === 'coach'

  const [plan, setPlan] = useState<WorkoutPlan | null>(null)
  const [clients, setClients] = useState<User[]>([])
  const [selectedClient, setSelectedClient] = useState('')
  const [startDate, setStartDate] = useState('')
  const [assigning, setAssigning] = useState(false)
  const [assignSuccess, setAssignSuccess] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!planId) return
    async function load() {
      try {
        const [planData, clientsData] = await Promise.all([
          getPlan(planId!),
          isCoach ? getClients() : Promise.resolve([]),
        ])
        setPlan(planData)
        setClients(clientsData)
      } catch {
        setError('Plan not found.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [planId, isCoach])

  async function handleAssign() {
    if (!planId || !selectedClient || !startDate) return
    setAssigning(true)
    try {
      await assignPlan(planId, selectedClient, startDate)
      setAssignSuccess(true)
      setSelectedClient('')
      setStartDate('')
    } catch {
      setError('Failed to assign plan.')
    } finally {
      setAssigning(false)
    }
  }

  async function handleDelete() {
    if (!planId || !confirm('Delete this plan? This cannot be undone.')) return
    try {
      await deletePlan(planId)
      navigate('/plans')
    } catch {
      setError('Failed to delete plan.')
    }
  }

  if (loading) return <div className={styles.loading}>Loading plan...</div>
  if (error || !plan) return <div className={styles.error}>{error ?? 'Plan not found.'}</div>

  return (
    <div className={styles.page}>
      <button onClick={() => navigate(-1)} className={styles.back}>← Back</button>

      <header className={styles.header}>
        <div className={styles.headerRow}>
          <h1>{plan.title}</h1>
          {isCoach && (
            <div className={styles.actions}>
              <Link to={`/plans/${plan.id}/edit`} className={styles.editBtn}>Edit</Link>
              <button onClick={handleDelete} className={styles.deleteBtn}>Delete</button>
            </div>
          )}
        </div>
        {plan.description && <p className={styles.description}>{plan.description}</p>}
        <p className={styles.meta}>
          {plan.workouts.length} day{plan.workouts.length !== 1 ? 's' : ''} ·{' '}
          Created {new Date(plan.created_at).toLocaleDateString()}
        </p>
      </header>

      {isCoach && clients.length > 0 && (
        <section className={styles.assignSection}>
          <h2>Assign to client</h2>
          <div className={styles.assignRow}>
            <select
              value={selectedClient}
              onChange={e => setSelectedClient(e.target.value)}
              className={styles.select}
            >
              <option value="">Select a client...</option>
              {clients.map(c => (
                <option key={c.id} value={c.id}>{c.name} ({c.email})</option>
              ))}
            </select>
            <input
              type="date"
              value={startDate}
              onChange={e => setStartDate(e.target.value)}
              className={styles.dateInput}
            />
            <button
              onClick={handleAssign}
              disabled={!selectedClient || !startDate || assigning}
              className={styles.assignButton}
            >
              {assigning ? 'Assigning...' : 'Assign'}
            </button>
          </div>
          {assignSuccess && <p className={styles.success}>Plan assigned successfully!</p>}
        </section>
      )}

      <div className={styles.workouts}>
        {plan.workouts.map(workout => (
          <section key={workout.id} className={styles.workoutCard}>
            <div className={styles.workoutHeader}>
              <span className={styles.workoutOrder}>Day {workout.order}</span>
              {workout.is_rest_day
                ? <span className={styles.restBadge}>Rest Day</span>
                : <h2 className={styles.workoutTitle}>{workout.title}</h2>
              }
            </div>
            {workout.notes && <p className={styles.workoutNotes}>{workout.notes}</p>}
            {!workout.is_rest_day && workout.exercises.length > 0 && (
              <div className={styles.exercises}>
                {workout.exercises.map(ex => (
                  <div key={ex.id} className={styles.exercise}>
                    <span className={styles.exLabel}>{ex.label}</span>
                    <div className={styles.exContent}>
                      <span className={styles.exName}>{ex.name}</span>
                      {ex.description && <p className={styles.exDescription}>{ex.description}</p>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Update `PlanDetailPage.module.css`**

Add the new styles (keep existing, add these):

```css
.headerRow { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.actions { display: flex; gap: 10px; flex-shrink: 0; }
.editBtn {
  background: #333;
  border: none;
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 8px 16px;
  text-decoration: none;
}
.editBtn:hover { background: #444; }
.deleteBtn {
  background: none;
  border: 1px solid #444;
  border-radius: 6px;
  color: #f87171;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 8px 16px;
}
.deleteBtn:hover { background: #1a1a1a; }
.dateInput {
  background: #111;
  border: 1px solid #333;
  border-radius: 6px;
  color: #fff;
  padding: 8px;
  font-size: 0.9rem;
}
.restBadge {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 4px;
  color: #888;
  font-size: 0.85rem;
  padding: 4px 10px;
}
.exercises { display: flex; flex-direction: column; gap: 8px; margin-top: 10px; }
.exercise { display: flex; gap: 12px; align-items: flex-start; }
.exLabel {
  background: #222;
  border-radius: 4px;
  color: #f97316;
  font-weight: 700;
  font-size: 0.85rem;
  padding: 4px 8px;
  min-width: 32px;
  text-align: center;
  flex-shrink: 0;
}
.exContent { display: flex; flex-direction: column; gap: 2px; }
.exName { color: #fff; font-size: 0.95rem; font-weight: 500; }
.exDescription { color: #888; font-size: 0.85rem; margin: 0; }
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/PlanDetailPage.tsx frontend/src/pages/PlanDetailPage.module.css
git commit -m "feat: update PlanDetailPage for new exercise model; add edit/delete; add start_date to assign"
```

---

### Task 12: Update ClientsPage with links

**Files:**
- Modify: `frontend/src/pages/ClientsPage.tsx`

- [ ] **Step 1: Add `Link` import and wrap client names**

In `ClientsPage.tsx`, import `Link` from `react-router-dom` and wrap the client name/email in the roster with a link to `/clients/:id`. Find the section that renders the client list and update the client row to include a link:

```tsx
import { Link } from 'react-router-dom'

// In the client list render, replace the plain client row with:
{clients.map(client => (
  <div key={client.id} className={styles.clientRow}>
    <Link to={`/clients/${client.id}`} className={styles.clientLink}>
      {client.name}
    </Link>
    <span className={styles.clientEmail}>{client.email}</span>
  </div>
))}
```

Add to `ClientsPage.module.css`:

```css
.clientLink { color: #f97316; text-decoration: none; font-weight: 500; }
.clientLink:hover { text-decoration: underline; }
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/ClientsPage.tsx frontend/src/pages/ClientsPage.module.css
git commit -m "feat: link client names to their program calendar"
```

---

### Task 13: useSchedule hook

**Files:**
- Create: `frontend/src/hooks/useSchedule.ts`

- [ ] **Step 1: Create `useSchedule.ts`**

```typescript
/**
 * useSchedule: fetches and manages a client's scheduled workouts for a date range.
 */

import { useCallback, useEffect, useState } from 'react'
import { getSchedule } from '@/api/schedule'
import type { ScheduledWorkout } from '@/types/schedule'

export function useSchedule(clientId: string, start: string, end: string) {
  const [workouts, setWorkouts] = useState<ScheduledWorkout[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(() => {
    setLoading(true)
    setError(null)
    getSchedule(clientId, start, end)
      .then(setWorkouts)
      .catch(() => setError('Failed to load schedule.'))
      .finally(() => setLoading(false))
  }, [clientId, start, end])

  useEffect(() => { reload() }, [reload])

  return { workouts, loading, error, reload }
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/hooks/useSchedule.ts
git commit -m "feat: add useSchedule hook"
```

---

### Task 14: ClientProgramPage

**Files:**
- Create: `frontend/src/pages/ClientProgramPage.tsx`
- Create: `frontend/src/pages/ClientProgramPage.module.css`

- [ ] **Step 1: Create `ClientProgramPage.tsx`**

```tsx
/**
 * ClientProgramPage: coach views and manages a client's workout calendar.
 * Month grid at top; clicking a week row expands the week detail strip below.
 * Coaches can apply plans, add one-off workouts, and edit any day inline.
 */

import { useState, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { useSchedule } from '@/hooks/useSchedule'
import { getPlans, assignPlan } from '@/api/plans'
import { createScheduledWorkout, updateScheduledWorkout, deleteScheduledWorkout } from '@/api/schedule'
import type { ScheduledWorkout, ScheduledExercisePayload } from '@/types/schedule'
import type { WorkoutPlan } from '@/types/plan'
import styles from './ClientProgramPage.module.css'

// ── Date helpers ────────────────────────────────────────────────────────────

function toYMD(d: Date): string {
  return d.toISOString().slice(0, 10)
}

function startOfMonth(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), 1)
}

function endOfMonth(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth() + 1, 0)
}

/** Returns an array of weeks; each week is 7 Dates (Mon–Sun). */
function getWeeksInMonth(month: Date): Date[][] {
  const first = startOfMonth(month)
  // Shift so week starts Monday (0=Sun → 6, 1=Mon → 0, ...)
  const startOffset = (first.getDay() + 6) % 7
  const start = new Date(first)
  start.setDate(first.getDate() - startOffset)

  const weeks: Date[][] = []
  const cur = new Date(start)
  while (cur <= endOfMonth(month) || weeks.length === 0) {
    const week: Date[] = []
    for (let i = 0; i < 7; i++) {
      week.push(new Date(cur))
      cur.setDate(cur.getDate() + 1)
    }
    weeks.push(week)
    if (cur > endOfMonth(month) && weeks.length >= 1) break
  }
  return weeks
}

function monthLabel(d: Date): string {
  return d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
}

function shortDay(d: Date): string {
  return d.toLocaleDateString('en-US', { weekday: 'short' })
}

function dayNum(d: Date): number {
  return d.getDate()
}

function isSameMonth(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth()
}

// ── Types ────────────────────────────────────────────────────────────────────

type ExerciseEdit = { _id: string; label: string; name: string; description: string }

interface EditState {
  workout: ScheduledWorkout | null
  date: string
  title: string
  notes: string
  isRestDay: boolean
  exercises: ExerciseEdit[]
}

function newExerciseEdit(): ExerciseEdit {
  return { _id: crypto.randomUUID(), label: '', name: '', description: '' }
}

function workoutToEdit(sw: ScheduledWorkout): EditState {
  return {
    workout: sw,
    date: sw.date,
    title: sw.title ?? '',
    notes: sw.notes ?? '',
    isRestDay: sw.is_rest_day,
    exercises: sw.exercises.map(ex => ({
      _id: ex.id,
      label: ex.label,
      name: ex.name,
      description: ex.description ?? '',
    })),
  }
}

function emptyEdit(date: string): EditState {
  return {
    workout: null,
    date,
    title: '',
    notes: '',
    isRestDay: false,
    exercises: [newExerciseEdit()],
  }
}

// ── Component ────────────────────────────────────────────────────────────────

export default function ClientProgramPage() {
  const { clientId } = useParams<{ clientId: string }>()
  const { user } = useAuth()
  const isCoach = user?.role === 'coach'

  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [selectedWeekStart, setSelectedWeekStart] = useState<string | null>(null)
  const [edit, setEdit] = useState<EditState | null>(null)
  const [saving, setSaving] = useState(false)

  // Apply plan modal state
  const [showApplyModal, setShowApplyModal] = useState(false)
  const [plans, setPlans] = useState<WorkoutPlan[]>([])
  const [selectedPlan, setSelectedPlan] = useState('')
  const [applyStartDate, setApplyStartDate] = useState('')
  const [applying, setApplying] = useState(false)
  const [applyError, setApplyError] = useState<string | null>(null)

  const monthStart = toYMD(startOfMonth(currentMonth))
  const monthEnd = toYMD(endOfMonth(currentMonth))

  const { workouts, loading, reload } = useSchedule(clientId!, monthStart, monthEnd)

  const workoutByDate = useMemo(() => {
    const map: Record<string, ScheduledWorkout> = {}
    for (const w of workouts) map[w.date] = w
    return map
  }, [workouts])

  const weeks = useMemo(() => getWeeksInMonth(currentMonth), [currentMonth])

  // Selected week days
  const selectedWeek = useMemo(() => {
    if (!selectedWeekStart) return null
    const start = new Date(selectedWeekStart + 'T00:00:00')
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date(start)
      d.setDate(start.getDate() + i)
      return d
    })
  }, [selectedWeekStart])

  function prevMonth() {
    setCurrentMonth(m => new Date(m.getFullYear(), m.getMonth() - 1, 1))
    setSelectedWeekStart(null)
    setEdit(null)
  }

  function nextMonth() {
    setCurrentMonth(m => new Date(m.getFullYear(), m.getMonth() + 1, 1))
    setSelectedWeekStart(null)
    setEdit(null)
  }

  function selectWeek(week: Date[]) {
    const key = toYMD(week[0])
    setSelectedWeekStart(prev => (prev === key ? null : key))
    setEdit(null)
  }

  function openEdit(date: string) {
    const existing = workoutByDate[date]
    setEdit(existing ? workoutToEdit(existing) : emptyEdit(date))
  }

  function updateEditEx(id: string, patch: Partial<ExerciseEdit>) {
    setEdit(e => e ? ({
      ...e,
      exercises: e.exercises.map(ex => ex._id === id ? { ...ex, ...patch } : ex),
    }) : e)
  }

  async function openApplyModal() {
    setApplyError(null)
    const data = await getPlans()
    setPlans(data)
    setShowApplyModal(true)
  }

  async function handleApplyPlan() {
    if (!selectedPlan || !applyStartDate || !clientId) return
    setApplying(true)
    setApplyError(null)
    try {
      await assignPlan(selectedPlan, clientId, applyStartDate)
      setShowApplyModal(false)
      setSelectedPlan('')
      setApplyStartDate('')
      reload()
    } catch {
      setApplyError('Failed to apply plan.')
    } finally {
      setApplying(false)
    }
  }

  async function handleSaveEdit() {
    if (!edit || !clientId) return
    setSaving(true)
    const exercises: ScheduledExercisePayload[] = edit.isRestDay
      ? []
      : edit.exercises.map((ex, i) => ({
          label: ex.label,
          name: ex.name,
          description: ex.description || undefined,
          order: i + 1,
        }))

    try {
      if (edit.workout) {
        await updateScheduledWorkout(clientId, edit.workout.id, {
          title: edit.title || undefined,
          notes: edit.notes || undefined,
          is_rest_day: edit.isRestDay,
          exercises,
        })
      } else {
        await createScheduledWorkout(clientId, {
          date: edit.date,
          title: edit.title || undefined,
          notes: edit.notes || undefined,
          is_rest_day: edit.isRestDay,
          exercises,
        })
      }
      setEdit(null)
      reload()
    } catch {
      // keep edit open on error
    } finally {
      setSaving(false)
    }
  }

  async function handleDeleteEdit() {
    if (!edit?.workout || !clientId) return
    if (!confirm('Delete this workout?')) return
    setSaving(true)
    try {
      await deleteScheduledWorkout(clientId, edit.workout.id)
      setEdit(null)
      reload()
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className={styles.page}>Loading...</div>

  return (
    <div className={styles.page}>
      <div className={styles.toolbar}>
        <h1 className={styles.heading}>Client Program</h1>
        {isCoach && (
          <button className={styles.applyBtn} onClick={openApplyModal}>Apply Plan</button>
        )}
      </div>

      {/* Month grid */}
      <div className={styles.calendar}>
        <div className={styles.monthNav}>
          <button onClick={prevMonth} className={styles.navBtn}>‹</button>
          <span className={styles.monthLabel}>{monthLabel(currentMonth)}</span>
          <button onClick={nextMonth} className={styles.navBtn}>›</button>
        </div>

        <div className={styles.dayHeaders}>
          {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(d => (
            <div key={d} className={styles.dayHeader}>{d}</div>
          ))}
        </div>

        {weeks.map((week, wi) => {
          const weekKey = toYMD(week[0])
          const isSelected = selectedWeekStart === weekKey
          return (
            <div
              key={wi}
              className={`${styles.weekRow} ${isSelected ? styles.weekRowSelected : ''}`}
              onClick={() => selectWeek(week)}
            >
              {week.map(day => {
                const ymd = toYMD(day)
                const sw = workoutByDate[ymd]
                const inMonth = isSameMonth(day, currentMonth)
                return (
                  <div key={ymd} className={`${styles.dayCell} ${!inMonth ? styles.dayCellOut : ''}`}>
                    <span className={styles.dayCellNum}>{dayNum(day)}</span>
                    {sw && (
                      <span className={`${styles.dayCellLabel} ${sw.is_rest_day ? styles.restLabel : ''}`}>
                        {sw.is_rest_day ? 'Rest' : (sw.title ?? 'Workout')}
                      </span>
                    )}
                  </div>
                )
              })}
            </div>
          )
        })}
      </div>

      {/* Week detail strip */}
      {selectedWeek && (
        <div className={styles.weekDetail}>
          <div className={styles.weekStrip}>
            {selectedWeek.map(day => {
              const ymd = toYMD(day)
              const sw = workoutByDate[ymd]
              const isEditing = edit?.date === ymd
              return (
                <div
                  key={ymd}
                  className={`${styles.dayColumn} ${isEditing ? styles.dayColumnActive : ''}`}
                  onClick={() => isCoach && openEdit(ymd)}
                >
                  <div className={styles.dayColumnHeader}>
                    <span className={styles.dayColumnDay}>{shortDay(day)}</span>
                    <span className={styles.dayColumnDate}>{dayNum(day)}</span>
                  </div>
                  {sw ? (
                    sw.is_rest_day ? (
                      <span className={styles.restBadge}>Rest</span>
                    ) : (
                      <div className={styles.workoutPreview}>
                        <div className={styles.workoutPreviewTitle}>{sw.title}</div>
                        {sw.exercises.map(ex => (
                          <div key={ex.id} className={styles.exRow}>
                            <span className={styles.exLabel}>{ex.label}</span>
                            <span className={styles.exName}>{ex.name}</span>
                          </div>
                        ))}
                      </div>
                    )
                  ) : (
                    isCoach && <span className={styles.emptyDay}>+ Add</span>
                  )}
                </div>
              )
            })}
          </div>

          {/* Inline editor */}
          {edit && isCoach && (
            <div className={styles.editor}>
              <div className={styles.editorHeader}>
                <span className={styles.editorDate}>{new Date(edit.date + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}</span>
                <label className={styles.restToggle}>
                  <input
                    type="checkbox"
                    checked={edit.isRestDay}
                    onChange={e => setEdit(ed => ed ? { ...ed, isRestDay: e.target.checked } : ed)}
                  />
                  Rest day
                </label>
                <button className={styles.editorClose} onClick={() => setEdit(null)}>✕</button>
              </div>

              {!edit.isRestDay && (
                <>
                  <input
                    className={styles.editorTitle}
                    placeholder="Workout title"
                    value={edit.title}
                    onChange={e => setEdit(ed => ed ? { ...ed, title: e.target.value } : ed)}
                  />
                  <textarea
                    className={styles.editorNotes}
                    placeholder="Notes (optional)"
                    value={edit.notes}
                    onChange={e => setEdit(ed => ed ? { ...ed, notes: e.target.value } : ed)}
                    rows={2}
                  />
                  <div className={styles.editorExercises}>
                    {edit.exercises.map(ex => (
                      <div key={ex._id} className={styles.editorEx}>
                        <input
                          className={styles.editorExLabel}
                          placeholder="A"
                          value={ex.label}
                          onChange={e => updateEditEx(ex._id, { label: e.target.value })}
                        />
                        <input
                          className={styles.editorExName}
                          placeholder="Exercise name"
                          value={ex.name}
                          onChange={e => updateEditEx(ex._id, { name: e.target.value })}
                        />
                        <textarea
                          className={styles.editorExDesc}
                          placeholder="Sets, reps, notes..."
                          value={ex.description}
                          onChange={e => updateEditEx(ex._id, { description: e.target.value })}
                          rows={2}
                        />
                        {edit.exercises.length > 1 && (
                          <button
                            className={styles.removeBtn}
                            onClick={() => setEdit(ed => ed ? { ...ed, exercises: ed.exercises.filter(e => e._id !== ex._id) } : ed)}
                          >✕</button>
                        )}
                      </div>
                    ))}
                    <button
                      className={styles.addExBtn}
                      onClick={() => setEdit(ed => ed ? { ...ed, exercises: [...ed.exercises, newExerciseEdit()] } : ed)}
                    >+ Add Block</button>
                  </div>
                </>
              )}

              <div className={styles.editorActions}>
                {edit.workout && (
                  <button onClick={handleDeleteEdit} className={styles.deleteBtn} disabled={saving}>Delete</button>
                )}
                <button onClick={handleSaveEdit} className={styles.saveBtn} disabled={saving}>
                  {saving ? 'Saving...' : 'Save'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Apply plan modal */}
      {showApplyModal && (
        <div className={styles.modalOverlay} onClick={e => e.target === e.currentTarget && setShowApplyModal(false)}>
          <div className={styles.modal}>
            <h2>Apply Plan</h2>
            <label className={styles.modalLabel}>Plan</label>
            <select
              className={styles.modalSelect}
              value={selectedPlan}
              onChange={e => setSelectedPlan(e.target.value)}
            >
              <option value="">Select a plan...</option>
              {plans.map(p => <option key={p.id} value={p.id}>{p.title}</option>)}
            </select>
            <label className={styles.modalLabel}>Start Date</label>
            <input
              type="date"
              className={styles.modalDate}
              value={applyStartDate}
              onChange={e => setApplyStartDate(e.target.value)}
            />
            {applyError && <p className={styles.applyError}>{applyError}</p>}
            <div className={styles.modalActions}>
              <button onClick={() => setShowApplyModal(false)} className={styles.cancelBtn}>Cancel</button>
              <button
                onClick={handleApplyPlan}
                disabled={!selectedPlan || !applyStartDate || applying}
                className={styles.confirmBtn}
              >
                {applying ? 'Applying...' : 'Apply'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Create `ClientProgramPage.module.css`**

```css
.page { max-width: 1000px; margin: 0 auto; padding: 32px 24px; }

.toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.heading { font-size: 1.8rem; color: #fff; }
.applyBtn { background: #f97316; border: none; border-radius: 8px; color: #000; cursor: pointer; font-weight: 700; padding: 10px 20px; }
.applyBtn:hover { background: #ea6c0a; }

/* Month calendar */
.calendar { background: #111; border: 1px solid #222; border-radius: 12px; overflow: hidden; margin-bottom: 24px; }
.monthNav { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid #222; }
.monthLabel { color: #fff; font-weight: 600; font-size: 1rem; }
.navBtn { background: none; border: 1px solid #333; border-radius: 6px; color: #ccc; cursor: pointer; font-size: 1.2rem; padding: 4px 12px; }
.navBtn:hover { border-color: #f97316; color: #f97316; }

.dayHeaders { display: grid; grid-template-columns: repeat(7, 1fr); border-bottom: 1px solid #222; }
.dayHeader { color: #555; font-size: 0.75rem; font-weight: 600; padding: 8px; text-align: center; text-transform: uppercase; }

.weekRow { display: grid; grid-template-columns: repeat(7, 1fr); border-bottom: 1px solid #1a1a1a; cursor: pointer; }
.weekRow:hover { background: #161616; }
.weekRowSelected { background: #1a1a1a; border-left: 3px solid #f97316; }
.weekRow:last-child { border-bottom: none; }

.dayCell { padding: 8px; min-height: 56px; display: flex; flex-direction: column; gap: 4px; }
.dayCellOut .dayCellNum { color: #333; }
.dayCellNum { color: #888; font-size: 0.8rem; }
.dayCellLabel { background: #f97316; border-radius: 3px; color: #000; font-size: 0.7rem; font-weight: 600; padding: 2px 5px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.restLabel { background: #222; color: #555; }

/* Week detail */
.weekDetail { background: #111; border: 1px solid #222; border-radius: 12px; overflow: hidden; }
.weekStrip { display: grid; grid-template-columns: repeat(7, 1fr); border-bottom: 1px solid #1a1a1a; }

.dayColumn { border-right: 1px solid #1a1a1a; cursor: pointer; min-height: 140px; padding: 12px 10px; display: flex; flex-direction: column; gap: 8px; }
.dayColumn:last-child { border-right: none; }
.dayColumn:hover { background: #161616; }
.dayColumnActive { background: #1a1a1a; border-top: 2px solid #f97316; }

.dayColumnHeader { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.dayColumnDay { color: #555; font-size: 0.7rem; text-transform: uppercase; }
.dayColumnDate { color: #fff; font-size: 1rem; font-weight: 600; }

.restBadge { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 4px; color: #555; font-size: 0.75rem; padding: 3px 8px; text-align: center; }
.emptyDay { color: #333; font-size: 0.8rem; text-align: center; margin-top: 8px; }

.workoutPreview { display: flex; flex-direction: column; gap: 4px; }
.workoutPreviewTitle { color: #f97316; font-size: 0.8rem; font-weight: 600; }
.exRow { display: flex; gap: 5px; align-items: baseline; }
.exLabel { color: #f97316; font-size: 0.7rem; font-weight: 700; }
.exName { color: #888; font-size: 0.75rem; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }

/* Inline editor */
.editor { padding: 20px; border-top: 1px solid #222; display: flex; flex-direction: column; gap: 12px; }
.editorHeader { display: flex; align-items: center; gap: 16px; }
.editorDate { color: #f97316; font-weight: 600; font-size: 0.95rem; flex: 1; }
.restToggle { display: flex; align-items: center; gap: 6px; color: #888; font-size: 0.85rem; cursor: pointer; }
.restToggle input { accent-color: #f97316; }
.editorClose { background: none; border: none; color: #555; cursor: pointer; font-size: 1.1rem; padding: 4px; }
.editorClose:hover { color: #ccc; }

.editorTitle {
  background: transparent;
  border: none;
  border-bottom: 1px solid #333;
  color: #fff;
  font-size: 1rem;
  outline: none;
  padding: 4px 0;
  width: 100%;
}
.editorTitle:focus { border-bottom-color: #f97316; }

.editorNotes {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 6px;
  color: #ccc;
  font-size: 0.9rem;
  padding: 8px;
  resize: vertical;
  width: 100%;
  box-sizing: border-box;
}
.editorNotes:focus { border-color: #f97316; outline: none; }

.editorExercises { display: flex; flex-direction: column; gap: 8px; }
.editorEx { display: grid; grid-template-columns: 44px 1fr; gap: 6px; background: #1a1a1a; border-radius: 6px; padding: 10px; }
.editorExLabel {
  grid-row: 1; grid-column: 1;
  background: #222; border: 1px solid #333; border-radius: 4px;
  color: #f97316; font-weight: 700; text-align: center; padding: 4px; outline: none;
}
.editorExLabel:focus { border-color: #f97316; }
.editorExName {
  grid-row: 1; grid-column: 2;
  background: transparent; border: none; border-bottom: 1px solid #333;
  color: #fff; padding: 4px 0; font-size: 0.9rem; outline: none;
}
.editorExName:focus { border-bottom-color: #f97316; }
.editorExDesc { grid-row: 2; grid-column: 1 / 3; background: #222; border: 1px solid #2a2a2a; border-radius: 4px; color: #ccc; font-size: 0.85rem; padding: 6px; resize: vertical; }
.editorExDesc:focus { border-color: #f97316; outline: none; }

.addExBtn { background: none; border: 1px dashed #333; border-radius: 6px; color: #f97316; cursor: pointer; font-size: 0.8rem; padding: 6px; width: 100%; }
.addExBtn:hover { border-color: #f97316; background: #1a1a1a; }

.removeBtn { background: none; border: none; color: #555; cursor: pointer; font-size: 0.8rem; grid-column: 2; justify-self: end; padding: 2px 4px; }
.removeBtn:hover { color: #f87171; }

.editorActions { display: flex; gap: 10px; justify-content: flex-end; }
.saveBtn { background: #f97316; border: none; border-radius: 6px; color: #000; cursor: pointer; font-weight: 700; padding: 8px 20px; }
.saveBtn:disabled { opacity: 0.5; cursor: not-allowed; }
.deleteBtn { background: none; border: 1px solid #444; border-radius: 6px; color: #f87171; cursor: pointer; padding: 8px 16px; }
.deleteBtn:hover { background: #1a1a1a; }

/* Apply plan modal */
.modalOverlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #111; border: 1px solid #333; border-radius: 12px; display: flex; flex-direction: column; gap: 12px; min-width: 360px; padding: 28px; }
.modal h2 { color: #fff; font-size: 1.2rem; margin: 0; }
.modalLabel { color: #888; font-size: 0.85rem; }
.modalSelect, .modalDate { background: #1a1a1a; border: 1px solid #333; border-radius: 6px; color: #fff; font-size: 0.95rem; padding: 8px; width: 100%; }
.modalSelect:focus, .modalDate:focus { border-color: #f97316; outline: none; }
.applyError { color: #f87171; font-size: 0.85rem; }
.modalActions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 8px; }
.cancelBtn { background: none; border: 1px solid #333; border-radius: 6px; color: #888; cursor: pointer; padding: 8px 16px; }
.cancelBtn:hover { border-color: #555; color: #ccc; }
.confirmBtn { background: #f97316; border: none; border-radius: 6px; color: #000; cursor: pointer; font-weight: 700; padding: 8px 20px; }
.confirmBtn:disabled { opacity: 0.5; cursor: not-allowed; }
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/ClientProgramPage.tsx frontend/src/pages/ClientProgramPage.module.css
git commit -m "feat: add ClientProgramPage with month+week calendar and inline workout editor"
```

---

### Task 15: Wire App.tsx routing

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Add new routes to `App.tsx`**

Read the current `App.tsx` to find the route list and add:

```tsx
import CreatePlanPage from '@/pages/CreatePlanPage'
import EditPlanPage from '@/pages/EditPlanPage'
import ClientProgramPage from '@/pages/ClientProgramPage'

// Add inside the Routes block (next to existing plan/client routes):
<Route path="/plans/new" element={<ProtectedRoute><CreatePlanPage /></ProtectedRoute>} />
<Route path="/plans/:planId/edit" element={<ProtectedRoute><EditPlanPage /></ProtectedRoute>} />
<Route path="/clients/:clientId" element={<ProtectedRoute><ClientProgramPage /></ProtectedRoute>} />
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: add routes for create/edit plan and client program calendar"
```

---

### Task 16: End-to-end verification

- [ ] **Step 1: Start the app**

```bash
docker-compose up
```

Wait for all three containers to be healthy.

- [ ] **Step 2: Run all backend tests**

```bash
docker-compose exec backend python -m pytest tests/ -v
```

Expected: all tests pass (test_health, test_auth, test_users, test_plans, test_schedule).

- [ ] **Step 3: Verify plan creation**

1. Log in as a coach at `http://localhost:3000`
2. Navigate to `/plans` → click "+ New Plan"
3. Fill in title, add two workout days and one rest day with exercise blocks (label, name, description)
4. Click "Create Plan" → redirected to plan detail page
5. Verify exercise blocks display with label + description (no sets/reps table)

- [ ] **Step 4: Verify plan edit and delete**

1. From the plan detail page, click "Edit"
2. Change a workout title and an exercise description → save
3. Verify changes appear on detail page
4. Click "Delete" → confirm → redirected to `/plans`
5. Verify plan is gone from the list

- [ ] **Step 5: Verify plan assignment and calendar**

1. Create a new plan with 3 workout days and 1 rest day
2. Navigate to `/clients` → click a client name → lands on `/clients/:id` calendar
3. Click "Apply Plan" → select the plan → pick a start date → confirm
4. Verify the month grid shows the 4 days populated
5. Click the relevant week row → verify week strip shows workouts with exercise blocks and rest day badge

- [ ] **Step 6: Verify inline editing**

1. In the week strip, click a populated day → inline editor opens
2. Edit the workout title and an exercise description → save
3. Verify the week strip updates without page reload
4. Click an empty day → editor opens with blank form → add a one-off workout → save → appears on calendar

- [ ] **Step 7: Verify plan template is unchanged**

1. Navigate to `/plans` → open the plan used in step 5
2. Verify its workouts and exercises are unchanged (editing the client's scheduled workout should not affect the template)
