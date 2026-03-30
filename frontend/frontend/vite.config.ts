import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_API_BASE_URL

  return {
    plugins: [react()],
    server: {
      port: 3000,
      proxy: {
        '/user': {
          target: apiTarget,
          changeOrigin: true,
        },
        '/oauth2': {
          target: apiTarget,
          changeOrigin: true,
        },
        '/shop': {
          target: apiTarget,
          changeOrigin: true,
          bypass: (req, res, options) => {
            if (req.headers.accept && req.headers.accept.includes('text/html')) {
              return req.url;
            }
          },
        },
        '/friends': {
          target: apiTarget,
          changeOrigin: true,
          bypass: (req, res, options) => {
            if (req.headers.accept && req.headers.accept.includes('text/html')) {
              return req.url;
            }
          },
        },
        '/saju': {
          target: apiTarget,
          changeOrigin: true,
          bypass: (req) => {
            if (req.headers.accept?.includes('text/html')) return req.url;
          },
        },
        '/wallet': {
          target: apiTarget,
          changeOrigin: true,
        },
        '/session': {
          target: apiTarget,
          changeOrigin: true,
        },
        '/unse': {
          target: apiTarget,
          changeOrigin: true,
          bypass: (req) => {
            if (req.headers.accept?.includes('text/html')) return req.url;
          },
        },
        '/cards': {
          target: apiTarget,
          changeOrigin: true,
          bypass: (req) => {
            if (req.headers.accept?.includes('text/html')) return req.url;
          },
        },
        '/compatibility': {
          target: apiTarget,
          changeOrigin: true,
          bypass: (req) => {
            if (req.headers.accept?.includes('text/html')) return req.url;
          },
        }
      }
    }
  }
})
