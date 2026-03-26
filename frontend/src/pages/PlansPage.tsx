/**
 * PlansPage: list view of all plans for the current user.
 * Coaches see plans they created; clients see plans assigned to them.
 */

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getPlans } from '@/api/plans'
import { useAuth } from '@/context/AuthContext'
import type { WorkoutPlan } from '@/types/plan'
import styles from './PlansPage.module.css'

export default function PlansPage() {
  const { user } = useAuth()
  const isCoach = user?.role === 'coach'

  const [plans, setPlans] = useState<WorkoutPlan[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getPlans()
      .then(setPlans)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className={styles.loading}>Loading plans...</div>

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>{isCoach ? 'My Plans' : 'My Assigned Plans'}</h1>
        {isCoach && (
          <Link to="/plans/new" className={styles.newButton}>
            + New Plan
          </Link>
        )}
      </div>

      {plans.length === 0 ? (
        <div className={styles.empty}>
          <p>{isCoach ? 'No plans yet.' : 'No plans have been assigned to you yet.'}</p>
          {isCoach && <Link to="/plans/new">Create your first plan →</Link>}
        </div>
      ) : (
        <div className={styles.grid}>
          {plans.map((plan) => (
            <Link to={`/plans/${plan.id}`} key={plan.id} className={styles.card}>
              <h2 className={styles.planTitle}>{plan.title}</h2>
              {plan.description && <p className={styles.description}>{plan.description}</p>}
              <div className={styles.meta}>
                <span>{plan.workouts.length} workout{plan.workouts.length !== 1 ? 's' : ''}</span>
                <span>{new Date(plan.created_at).toLocaleDateString()}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
