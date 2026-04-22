# M3: Workout Builder — Design Spec

**Date:** 2026-04-21
**Status:** Approved
**Milestone:** M3

---

## Overview

M3 delivers the core workout programming workflow for coaches: a reusable plan library and a per-client calendar where those plans (and one-off workouts) are scheduled and managed.

Two primary surfaces:
1. **Plan Library** — coaches create reusable workout plan templates and manage them (full CRUD)
2. **Client Program Calendar** — coaches open a client's page, see their schedule on a month+week calendar, apply plans, and add/edit workouts directly

---

## Exercise Block Model

All exercise content — in both plan templates and client schedules — uses a **hybrid label + free-text** model:

- **`label`** — position identifier: `A`, `B`, `C`, `B1`, `B2` (supersets share the same letter prefix)
- **`name`** — the movement name (e.g., "Bench Press")
- **`description`** — free-text field for all programming details (e.g., "5x5 @ 75% 1RM, rest 3 min between sets")
- **`order`** — 1-based integer for ordering within the workout

The existing structured fields (`sets`, `reps`, `duration_seconds`) are removed in favour of `description`. Coaches write freely — no dropdowns or rigid fields.

---

## Data Model Changes

### Modified: `Exercise` table

| Field | Change |
|---|---|
| `sets` | **Removed** |
| `reps` | **Removed** |
| `duration_seconds` | **Removed** |
| `notes` | **Removed** |
| `label` | **Added** — String, not nullable |
| `description` | **Added** — Text, nullable |

`name`, `order`, `workout_id` are unchanged. `notes` is removed — `description` replaces it entirely.

### Modified: `Workout` table

| Field | Change |
|---|---|
| `is_rest_day` | **Added** — Boolean, default False |

When `is_rest_day` is true, the workout has no exercise blocks. `title` is optional for rest days.

### Modified: `PlanAssignment` table

| Field | Change |
|---|---|
| `start_date` | **Added** — Date, not nullable |

Required when assigning a plan. Drives how workouts are placed on the client calendar.

### New: `ScheduledWorkout` table

One row per day on a client's calendar. Created by plan assignment or directly by the coach.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `client_id` | UUID FK → users | Client this workout belongs to |
| `coach_id` | UUID FK → users | Coach who programmed it |
| `date` | Date | Calendar date |
| `title` | String | Workout name (e.g., "Upper Body") |
| `notes` | Text | Optional free-form notes for the day |
| `is_rest_day` | Boolean | Default false |
| `source_plan_id` | UUID FK → workout_plans | Optional — set when created from a plan assignment |
| `created_at` | DateTime | |

### New: `ScheduledExercise` table

Exercise blocks belonging to a `ScheduledWorkout`. Independent copies — editing these does not affect the plan template.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `scheduled_workout_id` | UUID FK → scheduled_workouts | |
| `label` | String | A, B, B1, B2, C... |
| `name` | String | Movement name |
| `description` | Text | Free-text instructions |
| `order` | Integer | 1-based position |

---

## Plan Assignment Behaviour

When a coach assigns a plan to a client:

1. A `start_date` is required in the request body
2. The backend iterates through the plan's workouts in `order` sequence
3. For each workout, one `ScheduledWorkout` is created on a consecutive date starting from `start_date`
   - Day 1 workout → `start_date`
   - Day 2 workout → `start_date + 1 day`
   - Day 3 rest day → `start_date + 2 days` (rest days consume a calendar date)
4. For non-rest workouts, all exercise blocks are copied into `ScheduledExercise` rows
5. `source_plan_id` is set on each `ScheduledWorkout` for traceability

Once instantiated, scheduled workouts are fully independent of the plan template. Editing a scheduled workout does not affect the plan, and editing the plan does not affect already-scheduled workouts.

---

## API

### Plan Library (updated)

```
POST   /plans                   Create plan (exercise model updated)
GET    /plans                   List coach's plans
GET    /plans/{id}              Get single plan
PUT    /plans/{id}              Replace plan workouts/exercises wholesale (coach-only, owns plan)
DELETE /plans/{id}              Delete plan + cascade (coach-only, owns plan)
POST   /plans/{id}/assign       Assign plan to client — body: { client_id, start_date }
```

All write operations are coach-only. `PUT /plans/{id}` replaces the full workout/exercise structure (no partial patch).

### Client Schedule (new)

```
GET    /clients/{client_id}/schedule?start=YYYY-MM-DD&end=YYYY-MM-DD
POST   /clients/{client_id}/schedule
GET    /clients/{client_id}/schedule/{workout_id}
PUT    /clients/{client_id}/schedule/{workout_id}
DELETE /clients/{client_id}/schedule/{workout_id}
```

- All endpoints require the coach to own the coach–client relationship (enforced via `coach_client` table)
- `GET` with date range returns all `ScheduledWorkout` rows (including rest days) within the range, with nested `ScheduledExercise` blocks
- `POST` creates a one-off scheduled workout for a specific date
- `PUT` replaces the workout's exercise blocks wholesale (same pattern as plan update)
- Clients can `GET` their own schedule (read-only) — required for M4

---

## Frontend

### New / Updated Pages

| Route | Component | Description |
|---|---|---|
| `/plans/new` | `CreatePlanPage` | Single-page plan builder |
| `/plans/:id/edit` | `EditPlanPage` | Same builder, pre-populated |
| `/plans/:id` | `PlanDetailPage` (updated) | Adds Edit + Delete buttons |
| `/clients` | `ClientsPage` (updated) | Each client name links to their program page |
| `/clients/:id` | `ClientProgramPage` | Month + week calendar view |

### Plan Builder (`CreatePlanPage` / `EditPlanPage`)

Single scrollable page:
- Plan title + description fields at top
- List of days below — each day has a title, rest day toggle, and exercise blocks
- Each exercise block: label input, name input, free-text description textarea
- Add/remove days; add/remove exercise blocks within a day
- Rest day toggle hides exercise block inputs for that day
- Save → `POST /plans` (create) or `PUT /plans/{id}` (edit)
- Shared `PlanBuilderForm` component used by both pages

### Client Program Page (`ClientProgramPage`)

Layout: month grid at top, week detail strip below.

**Month grid:**
- Shows current month; prev/next navigation
- Each day cell: workout title or "Rest" label; empty days show a faint `+`
- Clicking a week row expands the week detail strip

**Week detail strip:**
- 7 day columns for the selected week
- Each day shows: workout title, rest day badge, and all exercise blocks (label · name · description)
- Clicking a day opens an inline edit panel
- Empty days show "+ Add Workout" and "+ Add Rest Day" affordances

**Apply Plan modal:**
- Triggered by "Apply Plan" button
- Coach selects a plan from their library (dropdown)
- Coach picks a start date (date picker)
- On confirm → `POST /plans/{id}/assign` → calendar refreshes

**Inline workout editor:**
- Opens below the clicked day in the week strip
- Same exercise block fields as the plan builder (label, name, description)
- Save → `PUT /clients/{id}/schedule/{workout_id}`
- Delete → `DELETE /clients/{id}/schedule/{workout_id}`

### New API Functions (`src/api/plans.ts` + `src/api/schedule.ts`)

- `updatePlan(planId, payload)` → `PUT /plans/{id}`
- `deletePlan(planId)` → `DELETE /plans/{id}`
- `getSchedule(clientId, start, end)` → `GET /clients/{id}/schedule`
- `createScheduledWorkout(clientId, payload)` → `POST /clients/{id}/schedule`
- `updateScheduledWorkout(clientId, workoutId, payload)` → `PUT /clients/{id}/schedule/{workoutId}`
- `deleteScheduledWorkout(clientId, workoutId)` → `DELETE /clients/{id}/schedule/{id}`

### New TypeScript Types (`src/types/schedule.ts`)

- `ScheduledExercise`
- `ScheduledWorkout` (with nested `ScheduledExercise[]`)
- `CreateScheduledWorkoutPayload`
- `UpdateScheduledWorkoutPayload`

Updated `src/types/plan.ts`:
- `Exercise` — remove `sets`, `reps`, `duration_seconds`; add `label`, `description`
- `WorkoutPayload` — same updates
- `ExercisePayload` — same updates

---

## Migrations

Two Alembic migrations:
1. **Modify existing tables** — add `label`/`description` to `exercises`, add `is_rest_day` to `workouts`, add `start_date` to `plan_assignments`, drop `sets`/`reps`/`duration_seconds` from `exercises`
2. **Create new tables** — `scheduled_workouts`, `scheduled_exercises`

Split into two migrations so rollback is clean if needed.

---

## Testing

### Backend (pytest — integration tests, no mocks)

**Plan CRUD:**
- Coach can create a plan with workouts, rest days, and exercise blocks (label + description)
- Coach can update a plan (wholesale replace)
- Coach can delete a plan; cascade removes workouts and exercises
- Non-owner coach cannot update or delete another coach's plan (404)

**Plan Assignment:**
- Assigning a plan creates `ScheduledWorkout` rows on consecutive dates from `start_date`
- Rest days in the plan produce `ScheduledWorkout` rows with `is_rest_day=True` and no exercise blocks
- Exercise blocks are copied correctly into `ScheduledExercise` rows
- `source_plan_id` is set on all created `ScheduledWorkout` rows
- Duplicate assignment to same client returns 400

**Client Schedule CRUD:**
- Coach can create a one-off scheduled workout for their client
- Coach can update a scheduled workout; changes do not affect the source plan
- Coach can delete a scheduled workout
- Coach cannot access another coach's client schedule (403/404)
- Client can read their own schedule; client cannot write to it (403)

**Date range filtering:**
- `GET /clients/{id}/schedule?start=...&end=...` returns only workouts within range
- Rest days are included in the response

### Frontend

Manual end-to-end verification:
- Create a plan with workouts, rest days, and exercise blocks → plan appears in library
- Assign plan to a client with a start date → client calendar populates correctly
- Edit a scheduled workout → changes are saved; plan template is unchanged
- Add a one-off workout to an empty day → appears on calendar
- Delete a plan → removed from library; existing scheduled workouts are unaffected

---

## Key Decisions

- **Free-text over structured fields** — coaches program in natural language; rigid sets/reps fields don't accommodate AMRAP, percentages, or tempo prescriptions
- **Copy-on-assignment** — scheduled workouts are independent copies, not references. Editing a client's workout doesn't change the template. Editing the template doesn't retroactively change a client's schedule.
- **Wholesale PUT for updates** — plan and scheduled workout updates replace the full exercise block list rather than supporting granular patch operations. Simpler API surface; M3 scope doesn't require partial updates.
- **Two migrations** — keeps the schema migration history clean and rollback safe
- **`source_plan_id` on ScheduledWorkout** — retained for display purposes (e.g., "Applied from: Summer Shred Plan") and potential future features, but not used for data integrity
