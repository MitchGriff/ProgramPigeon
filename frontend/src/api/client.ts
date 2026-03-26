/**
 * Axios instance used for all API calls.
 *
 * - baseURL points to /api so the Vite proxy (dev) and nginx (prod) both route correctly
 * - withCredentials: true is required so httpOnly auth cookies are sent with every request
 * - On 401 responses, the user is redirected to /login
 */

import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api/v1',
  withCredentials: true, // Send cookies with every request (required for httpOnly JWT cookies)
  headers: {
    'Content-Type': 'application/json',
  },
})

// Redirect to login on 401 Unauthorized (expired or missing token)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
