/**
 * AuthContext: provides the current user and auth actions (login, logout, register)
 * to the entire component tree.
 *
 * On mount, it calls /auth/me to restore session state from the existing cookie
 * so the user stays logged in across page refreshes.
 */

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { getMe, login, logout as logoutApi, register } from '@/api/auth'
import type { LoginPayload, RegisterPayload, User } from '@/types/user'

interface AuthContextValue {
  /** The currently authenticated user, or null if not logged in. */
  user: User | null
  /** True while the initial session check is in progress. */
  loading: boolean
  /** Log in with email and password. */
  login: (payload: LoginPayload) => Promise<void>
  /** Register a new account. */
  register: (payload: RegisterPayload) => Promise<void>
  /** Log out the current user. */
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

/**
 * Wrap the app in AuthProvider to make auth state available everywhere.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // On mount: try to restore session from the existing httpOnly cookie
  useEffect(() => {
    getMe()
      .then(setUser)
      .finally(() => setLoading(false))
  }, [])

  async function handleLogin(payload: LoginPayload) {
    const loggedInUser = await login(payload)
    setUser(loggedInUser)
  }

  async function handleRegister(payload: RegisterPayload) {
    const newUser = await register(payload)
    setUser(newUser)
  }

  async function handleLogout() {
    await logoutApi()
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login: handleLogin,
        register: handleRegister,
        logout: handleLogout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

/**
 * Hook to access auth state and actions from any component.
 * Must be used inside AuthProvider.
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
