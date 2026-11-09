import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // While developing, any request to /api is forwarded to the Flask
    // backend. So in React we can simply call fetch("/api/route").
    proxy: {
      '/api': 'http://127.0.0.1:5000',
    },
  },
})
