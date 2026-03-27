/**
 * PlanDetailPage: displays a single workout plan with all its workouts and exercises.
 * Coaches can also assign the plan to a client from this page.
 */

import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getPlan, assignPlan } from '@/api/plans'
import { getClients } from '@/api/users'
import { useAuth } from '@/context/AuthContext'
import type { WorkoutPlan } from '@/types/plan'
import type { User } from '@/types/user'
import styles from './PlanDetailPage.module.css'

export default function PlanDetailPage() {
  const { planId } = useParams<{ planId: string }>()
  const { user } = useAuth()
  const navigate = useNavigate()
  const isCoach = user?.role === 'coach'

  const [plan, setPlan] = useState<WorkoutPlan | null>(null)
  const [clients, setClients] = useState<User[]>([])
  const [selectedClient, setSelectedClient] = useState('')
  const [assigning, setAssigning] = useState(false)
  const [assignSuccess, setAssignSuccess] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!planId) return
    async function load() {
      try {
        const [planData, clientsData] = await Promise.all([
          getPlan(planId!),
          isCoach ? getClients() : Promise.resolve([]),
        ])
        setPlan(planData)
        setClients(clientsData)
      } catch {
        setError('Plan not found.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [planId, isCoach])

  async function handleAssign() {
    if (!planId || !selectedClient) return
    setAssigning(true)
    try {
      await assignPlan(planId, selectedClient)
      setAssignSuccess(true)
      setSelectedClient('')
    } catch {
      setError('Failed to assign plan.')
    } finally {
      setAssigning(false)
    }
  }

  if (loading) return <div className={styles.loading}>Loading plan...</div>
  if (error || !plan) return <div className={styles.error}>{error ?? 'Plan not found.'}</div>

  return (
    <div className={styles.page}>
      <button onClick={() => navigate(-1)} className={styles.back}>
        ← Back
      </button>

      <header className={styles.header}>
        <h1>{plan.title}</h1>
        {plan.description && <p className={styles.description}>{plan.description}</p>}
        <p className={styles.meta}>
          {plan.workouts.length} workout{plan.workouts.length !== 1 ? 's' : ''} ·{' '}
          Created {new Date(plan.created_at).toLocaleDateString()}
        </p>
      </header>

      {/* Assign to client (coaches only) */}
      {isCoach && clients.length > 0 && (
        <section className={styles.assignSection}>
          <h2>Assign to client</h2>
          <div className={styles.assignRow}>
            <select
              value={selectedClient}
              onChange={(e) => setSelectedClient(e.target.value)}
              className={styles.select}
            >
              <option value="">Select a client...</option>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.email})
                </option>
              ))}
            </select>
            <button
              onClick={handleAssign}
              disabled={!selectedClient || assigning}
              className={styles.assignButton}
            >
              {assigning ? 'Assigning...' : 'Assign'}
            </button>
          </div>
          {assignSuccess && <p className={styles.success}>Plan assigned successfully!</p>}
        </section>
      )}

      {/* Workouts */}
      <div className={styles.workouts}>
        {plan.workouts.map((workout) => (
          <section key={workout.id} className={styles.workoutCard}>
            <div className={styles.workoutHeader}>
              <span className={styles.workoutOrder}>Day {workout.order}</span>
              <h2 className={styles.workoutTitle}>{workout.title}</h2>
            </div>
            {workout.notes && <p className={styles.workoutNotes}>{workout.notes}</p>}

            <table className={styles.exerciseTable}>
              <thead>
                <tr>
                  <th>Exercise</th>
                  <th>Sets</th>
                  <th>Reps</th>
                  <th>Duration</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {workout.exercises.map((ex) => (
                  <tr key={ex.id}>
                    <td className={styles.exerciseName}>{ex.name}</td>
                    <td>{ex.sets ?? '—'}</td>
                    <td>{ex.reps ?? '—'}</td>
                    <td>{ex.duration_seconds ? `${ex.duration_seconds}s` : '—'}</td>
                    <td className={styles.exerciseNotes}>{ex.notes ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        ))}
      </div>
    </div>
  )
}
