/**
 * Axios instance used for all API calls.
 *
 * - baseURL points to /api so the Vite proxy (dev) and nginx (prod) both route correctly
 * - withCredentials: true is required so httpOnly auth cookies are sent with every request
 * - On 401 responses, silently attempts a token refresh before redirecting to /login
 */

import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api/v1',
  withCredentials: true, // Send cookies with every request (required for httpOnly JWT cookies)
  headers: {
    'Content-Type': 'application/json',
  },
})

// Attempt a silent token refresh on 401, then retry the original request.
// If the refresh also fails, redirect to /login.
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const is401 = error.response?.status === 401
    const isRefreshEndpoint = originalRequest?.url === '/auth/refresh'

    // Only attempt refresh once, and never for the refresh endpoint itself
    if (is401 && !isRefreshEndpoint && !originalRequest._retry) {
      originalRequest._retry = true
      try {
        await apiClient.post('/auth/refresh')
        // Cookies updated — retry the original request
        return apiClient(originalRequest)
      } catch {
        // Refresh failed — fall through to redirect
      }
    }

    // Redirect to login for unrecoverable 401s
    if (is401 && window.location.pathname !== '/login') {
      window.location.href = '/login'
    }

    return Promise.reject(error)
  },
)

export default apiClient
