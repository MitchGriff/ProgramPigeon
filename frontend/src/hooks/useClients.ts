/**
 * useClients: manages the coach's client roster.
 *
 * Fetches clients on mount and exposes an addClient function that
 * calls the by-email endpoint and appends the result to local state
 * without requiring a refetch.
 */

import { useState, useEffect } from 'react'
import { getClients, addClientByEmail } from '@/api/users'
import type { User } from '@/types/user'

interface UseClientsResult {
  /** The coach's current client roster. */
  clients: User[]
  /** True while the initial fetch is in progress. */
  loading: boolean
  /** Error message if the initial fetch failed, otherwise null. */
  error: string | null
  /**
   * Add a client by email. Appends to the roster on success.
   * Throws on failure so the caller can display the error.
   */
  addClient: (email: string) => Promise<void>
}

export function useClients(): UseClientsResult {
  const [clients, setClients] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getClients()
      .then(setClients)
      .catch(() => setError('Failed to load clients.'))
      .finally(() => setLoading(false))
  }, [])

  async function addClient(email: string): Promise<void> {
    const newClient = await addClientByEmail(email)
    setClients((prev) => [...prev, newClient])
  }

  return { clients, loading, error, addClient }
}
