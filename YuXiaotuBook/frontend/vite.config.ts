import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5188,
    strictPort: true,
    proxy: {
      '/api/v1/orders': { target: 'http://127.0.0.1:8081', changeOrigin: true },
      '/api/v1/member': { target: 'http://127.0.0.1:8081', changeOrigin: true },
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/uploads': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/media': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/placeholders': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
