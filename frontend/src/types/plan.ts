/** A single exercise within a workout. */
export interface Exercise {
  id: string
  workout_id: string
  name: string
  sets: number | null
  reps: number | null
  duration_seconds: number | null
  notes: string | null
  order: number
}

/** A single workout session within a plan (e.g. "Day 1 - Upper Body"). */
export interface Workout {
  id: string
  plan_id: string
  title: string
  order: number
  notes: string | null
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
  assigned_at: string
}

/** Request body for creating an exercise. */
export interface ExercisePayload {
  name: string
  sets?: number
  reps?: number
  duration_seconds?: number
  notes?: string
  order: number
}

/** Request body for creating a workout. */
export interface WorkoutPayload {
  title: string
  order: number
  notes?: string
  exercises: ExercisePayload[]
}

/** Request body for creating a workout plan. */
export interface CreatePlanPayload {
  title: string
  description?: string
  workouts: WorkoutPayload[]
}
