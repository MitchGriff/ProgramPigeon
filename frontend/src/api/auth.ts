/**
 * Auth API functions: register, login, logout, and fetch current user.
 * Tokens are handled server-side via httpOnly cookies — no token management needed here.
 */

import apiClient from './client'
import type { LoginPayload, RegisterPayload, User } from '@/types/user'

/**
 * Register a new coach or client account.
 * Sets auth cookies on success.
 */
export async function register(payload: RegisterPayload): Promise<User> {
  const { data } = await apiClient.post<User>('/auth/register', payload)
  return data
}

/**
 * Log in with email and password.
 * Sets auth cookies on success.
 */
export async function login(payload: LoginPayload): Promise<User> {
  const { data } = await apiClient.post<User>('/auth/login', payload)
  return data
}

/**
 * Log out the current user.
 * Clears auth cookies server-side.
 */
export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout')
}

/**
 * Fetch the currently authenticated user.
 * Returns null if not authenticated (catches 401 without redirecting).
 */
export async function getMe(): Promise<User | null> {
  try {
    const { data } = await apiClient.get<User>('/auth/me')
    return data
  } catch {
    return null
  }
}
