<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { request } from '@/api/client'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const store = useUserStore()
const form = ref({ username: '', password: '' })
const error = ref('')

async function submit() {
  error.value = ''
  const res = await request<any>({
    url: '/auth/login',
    method: 'POST',
    data: form.value,
  })
  if (res.code === 200) {
    store.setAuth(res.data.token, res.data.user)
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } else {
    error.value = res.msg
  }
}
</script>

<template>
  <div class="container auth-page">
    <form class="auth-box" @submit.prevent="submit">
      <h1>登录</h1>
      <input v-model="form.username" placeholder="用户名" required />
      <input v-model="form.password" type="password" placeholder="密码" required />
      <p v-if="error" class="error">{{ error }}</p>
      <button class="btn btn-primary" type="submit">登录</button>
      <router-link to="/register">没有账号？注册</router-link>
    </form>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  padding: 64px 20px;
}
.auth-box {
  width: 360px;
  background: var(--color-surface);
  padding: 32px;
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.auth-box input {
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
}
.error { color: #c00; font-size: 14px; }

@media (max-width: 767px) {
  .auth-box { width: 100%; padding: 24px; }
}
</style>
