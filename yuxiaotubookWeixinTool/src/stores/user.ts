import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import * as authApi from '@/api/auth'
import type { UserInfo } from '@/types/user'
import {
  clearAuth,
  getStoredUser,
  getToken,
  setStoredUser,
  setToken,
} from '@/utils/storage'

export const useUserStore = defineStore('user', () => {
  const token = ref(getToken())
  const user = ref<UserInfo | null>(getStoredUser<UserInfo>())

  const isLoggedIn = computed(() => !!token.value)
  const isVip = computed(() => !!user.value?.is_vip)

  function setAuth(t: string, u: UserInfo) {
    token.value = t
    user.value = u
    setToken(t)
    setStoredUser(u)
  }

  function logout() {
    token.value = ''
    user.value = null
    clearAuth()
  }

  async function login(username: string, password: string) {
    const data = await authApi.login(username, password)
    setAuth(data.token, data.user)
    await fetchMe()
  }

  async function register(payload: {
    username: string
    password: string
    nickname?: string
    province?: string
    city?: string
  }) {
    const data = await authApi.register(payload)
    setAuth(data.token, data.user)
    await fetchMe()
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      const me = await authApi.fetchMe()
      user.value = me
      setStoredUser(me)
    } catch {
      logout()
    }
  }

  return { token, user, isLoggedIn, isVip, setAuth, logout, login, register, fetchMe }
})
