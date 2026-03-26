import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

/**
 * Vite config for ProgramPigeon frontend.
 * The /api proxy routes API requests to the FastAPI backend during development,
 * matching the nginx proxy config used in production.
 */
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      // Forward /api requests to the FastAPI backend
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})
