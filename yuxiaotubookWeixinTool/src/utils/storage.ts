const TOKEN_KEY = 'yxt_token'
const USER_KEY = 'yxt_user'

export function getToken(): string {
  return uni.getStorageSync(TOKEN_KEY) || ''
}

export function setToken(token: string) {
  uni.setStorageSync(TOKEN_KEY, token)
}

export function clearToken() {
  uni.removeStorageSync(TOKEN_KEY)
}

export function getStoredUser<T>(): T | null {
  const raw = uni.getStorageSync(USER_KEY)
  if (!raw) return null
  try {
    return typeof raw === 'string' ? JSON.parse(raw) : raw
  } catch {
    return null
  }
}

export function setStoredUser(user: unknown) {
  uni.setStorageSync(USER_KEY, JSON.stringify(user))
}

export function clearStoredUser() {
  uni.removeStorageSync(USER_KEY)
}

export function clearAuth() {
  clearToken()
  clearStoredUser()
}
