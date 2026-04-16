/**
 * Navbar: top navigation bar shown on all authenticated pages.
 * Shows the logo, nav links, and a logout button.
 * Coach and client see slightly different links.
 */

import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import styles from './Navbar.module.css'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  return (
    <nav className={styles.navbar}>
      <Link to="/dashboard" className={styles.brand}>
        <img src="/images/ProgramPigeon-logo3.jpg" alt="ProgramPigeon" className={styles.logo} />
        <span>ProgramPigeon</span>
      </Link>

      <div className={styles.links}>
        <NavLink
          to="/dashboard"
          className={({ isActive }) => (isActive ? styles.linkActive : styles.link)}
        >
          Dashboard
        </NavLink>
        <NavLink
          to="/plans"
          className={({ isActive }) => (isActive ? styles.linkActive : styles.link)}
        >
          Plans
        </NavLink>
        {user?.role === 'coach' && (
          <NavLink
            to="/clients"
            className={({ isActive }) => (isActive ? styles.linkActive : styles.link)}
          >
            Clients
          </NavLink>
        )}
        <NavLink
          to="/messages"
          className={({ isActive }) => (isActive ? styles.linkActive : styles.link)}
        >
          Messages
        </NavLink>
      </div>

      <div className={styles.user}>
        <span className={styles.userName}>{user?.name}</span>
        <button onClick={handleLogout} className={styles.logoutButton}>
          Sign out
        </button>
      </div>
    </nav>
  )
}
