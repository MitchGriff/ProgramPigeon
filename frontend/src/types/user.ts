/** The two account roles in ProgramPigeon. */
export type UserRole = 'coach' | 'client'

/** A user returned from the API. Never includes a password. */
export interface User {
  id: string
  email: string
  name: string
  role: UserRole
  created_at: string
}

/** Request body for POST /api/v1/auth/register */
export interface RegisterPayload {
  email: string
  name: string
  password: string
  role: UserRole
}

/** Request body for POST /api/v1/auth/login */
export interface LoginPayload {
  email: string
  password: string
}
