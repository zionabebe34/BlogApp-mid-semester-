import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// Every /api request from the browser is forwarded to the Flask backend.
// BACKEND_HOST/BACKEND_PORT let this point at a backend that isn't on
// localhost — e.g. the `backend` service name inside Docker Compose.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: {
      '/api': `http://${process.env.BACKEND_HOST || '127.0.0.1'}:${process.env.BACKEND_PORT || 5001}`,
    }
  }
})
