import { createSSRApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { API_BASE, MP_CLIENT_VERSION, TRADE_API_BASE } from '@/config/env'

export function createApp() {
  console.log('[YXT-MP]', MP_CLIENT_VERSION, { API_BASE, TRADE_API_BASE })
  const app = createSSRApp(App)
  app.use(createPinia())
  return { app }
}
