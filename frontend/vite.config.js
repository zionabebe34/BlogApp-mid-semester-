import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// Every /api request from the browser is forwarded to the Flask backend.
// BACKEND_PORT lets you match a backend started with a custom PORT
// (macOS AirPlay sometimes occupies the default port 5000).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': `http://127.0.0.1:${process.env.BACKEND_PORT || 5001}`,
    }
  }
})
