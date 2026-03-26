/**
 * Workout plan API functions: create, fetch, and assign plans.
 */

import apiClient from './client'
import type { CreatePlanPayload, PlanAssignment, WorkoutPlan } from '@/types/plan'

/**
 * Fetch all plans for the current user.
 * Coaches receive plans they created; clients receive plans assigned to them.
 */
export async function getPlans(): Promise<WorkoutPlan[]> {
  const { data } = await apiClient.get<WorkoutPlan[]>('/plans')
  return data
}

/**
 * Fetch a single plan by ID.
 */
export async function getPlan(planId: string): Promise<WorkoutPlan> {
  const { data } = await apiClient.get<WorkoutPlan>(`/plans/${planId}`)
  return data
}

/**
 * Create a new workout plan (coaches only).
 */
export async function createPlan(payload: CreatePlanPayload): Promise<WorkoutPlan> {
  const { data } = await apiClient.post<WorkoutPlan>('/plans', payload)
  return data
}

/**
 * Assign a plan to a client (coaches only).
 *
 * @param planId - The plan to assign.
 * @param clientId - The client to assign it to.
 */
export async function assignPlan(planId: string, clientId: string): Promise<PlanAssignment> {
  const { data } = await apiClient.post<PlanAssignment>(`/plans/${planId}/assign`, {
    client_id: clientId,
  })
  return data
}
