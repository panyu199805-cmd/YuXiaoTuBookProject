import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

export default defineConfig({
  plugins: [uni()],
  optimizeDeps: {
    include: ['pinia', 'vue', 'vue-demi'],
  },
})
