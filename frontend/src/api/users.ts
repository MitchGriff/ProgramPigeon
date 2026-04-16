/**
 * User management API functions: coach-client relationship management.
 */

import apiClient from './client'
import type { User } from '@/types/user'

/**
 * Fetch all clients linked to the authenticated coach.
 */
export async function getClients(): Promise<User[]> {
  const { data } = await apiClient.get<User[]>('/users/clients')
  return data
}

/**
 * Add a client to the authenticated coach's roster by user ID.
 */
export async function addClient(clientId: string): Promise<User> {
  const { data } = await apiClient.post<User>(`/users/clients/${clientId}`)
  return data
}

/**
 * Remove a client from the authenticated coach's roster.
 */
export async function removeClient(clientId: string): Promise<void> {
  await apiClient.delete(`/users/clients/${clientId}`)
}

/**
 * Add a client to the authenticated coach's roster by email address.
 * Throws if the email is not found or belongs to a non-client account.
 */
export async function addClientByEmail(email: string): Promise<User> {
  const { data } = await apiClient.post<User>('/users/clients/by-email', { email })
  return data
}
