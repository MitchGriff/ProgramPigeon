/**
 * ProtectedRoute: wraps routes that require authentication.
 * Redirects unauthenticated users to /login.
 * Shows nothing while the initial auth check is in progress.
 */

import { Navigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
}

export default function ProtectedRoute({ children }: Props) {
  const { user, loading } = useAuth()

  // Wait for the session check to complete before rendering or redirecting
  if (loading) return null

  if (!user) return <Navigate to="/login" replace />

  return <>{children}</>
}
