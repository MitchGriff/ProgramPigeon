/**
 * DashboardPage: the home screen after login.
 * Coaches see their client roster and quick links.
 * Clients see their assigned plans and quick links.
 */

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { getClients } from '@/api/users'
import { getPlans } from '@/api/plans'
import type { User } from '@/types/user'
import type { WorkoutPlan } from '@/types/plan'
import styles from './DashboardPage.module.css'

export default function DashboardPage() {
  const { user } = useAuth()
  const isCoach = user?.role === 'coach'

  const [clients, setClients] = useState<User[]>([])
  const [plans, setPlans] = useState<WorkoutPlan[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [plansData, clientsData] = await Promise.all([
          getPlans(),
          isCoach ? getClients() : Promise.resolve([]),
        ])
        setPlans(plansData)
        setClients(clientsData)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [isCoach])

  if (loading) return <div className={styles.loading}>Loading...</div>

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1>Welcome, {user?.name}</h1>
        <p className={styles.role}>{isCoach ? 'Coach' : 'Client'} account</p>
      </header>

      <div className={styles.grid}>
        {/* Plans card */}
        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <h2>{isCoach ? 'My Plans' : 'Assigned Plans'}</h2>
            {isCoach && (
              <Link to="/plans/new" className={styles.linkButton}>
                + New Plan
              </Link>
            )}
          </div>
          {plans.length === 0 ? (
            <p className={styles.empty}>
              {isCoach ? 'No plans yet. Create your first one!' : 'No plans assigned yet.'}
            </p>
          ) : (
            <ul className={styles.list}>
              {plans.map((plan) => (
                <li key={plan.id}>
                  <Link to={`/plans/${plan.id}`} className={styles.listItem}>
                    <span className={styles.planTitle}>{plan.title}</span>
                    <span className={styles.planMeta}>
                      {plan.workouts.length} workout{plan.workouts.length !== 1 ? 's' : ''}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
          <Link to="/plans" className={styles.viewAll}>
            View all plans →
          </Link>
        </section>

        {/* Clients card (coaches only) */}
        {isCoach && (
          <section className={styles.card}>
            <div className={styles.cardHeader}>
              <h2>My Clients</h2>
              <Link to="/clients" className={styles.linkButton}>
                Manage clients →
              </Link>
            </div>
            {clients.length === 0 ? (
              <p className={styles.empty}>No clients yet.</p>
            ) : (
              <ul className={styles.list}>
                {clients.map((client) => (
                  <li key={client.id}>
                    <Link to={`/messages/${client.id}`} className={styles.listItem}>
                      <span className={styles.planTitle}>{client.name}</span>
                      <span className={styles.planMeta}>{client.email}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}

        {/* Quick links card */}
        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <h2>Quick links</h2>
          </div>
          <ul className={styles.quickLinks}>
            <li><Link to="/plans">Workout Plans</Link></li>
            <li><Link to="/messages">Messages</Link></li>
          </ul>
        </section>
      </div>
    </div>
  )
}
