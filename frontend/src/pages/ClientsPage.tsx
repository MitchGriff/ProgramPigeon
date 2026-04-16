/**
 * ClientsPage: coach-only page for managing the client roster.
 *
 * Shows the full client list and an add-by-email form.
 * Redirects non-coach users to /dashboard.
 */

import { useState, type FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { useClients } from '@/hooks/useClients'
import styles from './ClientsPage.module.css'

export default function ClientsPage() {
  const { user } = useAuth()
  const { clients, loading, error, addClient } = useClients()

  const [email, setEmail] = useState('')
  const [addError, setAddError] = useState<string | null>(null)
  const [adding, setAdding] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Redirect non-coaches — they have no business here
  if (user?.role !== 'coach') return <Navigate to="/dashboard" replace />

  async function handleAddClient(e: FormEvent) {
    e.preventDefault()
    setAddError(null)
    setSuccessMessage(null)
    setAdding(true)
    try {
      await addClient(email)
      setSuccessMessage(`${email} added to your roster.`)
      setEmail('')
    } catch (err: unknown) {
      const detail =
        err instanceof Error ? err.message : 'No client account found with that email.'
      setAddError(detail)
    } finally {
      setAdding(false)
    }
  }

  if (loading) return <div className={styles.loading}>Loading clients...</div>
  if (error) return <div className={styles.error}>{error}</div>

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>My Clients</h1>

      {/* Add client form */}
      <section className={styles.card}>
        <h2 className={styles.cardTitle}>Add a client</h2>
        <p className={styles.cardDescription}>
          Enter the email address of an existing client account.
        </p>
        <form onSubmit={handleAddClient} className={styles.form}>
          <input
            type="email"
            className={styles.input}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="client@example.com"
            required
            autoComplete="off"
          />
          <button type="submit" className={styles.button} disabled={adding}>
            {adding ? 'Adding...' : 'Add client'}
          </button>
        </form>
        {addError && <p className={styles.addError}>{addError}</p>}
        {successMessage && <p className={styles.success}>{successMessage}</p>}
      </section>

      {/* Client roster */}
      <section className={styles.card}>
        <h2 className={styles.cardTitle}>
          Client roster
          <span className={styles.count}>{clients.length}</span>
        </h2>
        {clients.length === 0 ? (
          <p className={styles.empty}>No clients yet. Add your first client above.</p>
        ) : (
          <ul className={styles.list}>
            {clients.map((client) => (
              <li key={client.id} className={styles.listItem}>
                <Link to={`/messages/${client.id}`} className={styles.clientLink}>
                  <span className={styles.clientName}>{client.name}</span>
                  <span className={styles.clientEmail}>{client.email}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
