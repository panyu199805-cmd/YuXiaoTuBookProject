import { fetchData, get, post } from './client'
import type { UserInfo } from '@/types/user'

export function login(username: string, password: string) {
  return fetchData(
    post<{ token: string; user: UserInfo }>('/auth/login', { username, password }, false),
  )
}

export function register(payload: {
  username: string
  password: string
  nickname?: string
  province?: string
  city?: string
}) {
  return fetchData(
    post<{ token: string; user: UserInfo }>('/auth/register', payload, false),
  )
}

export function fetchMe() {
  return fetchData(get<UserInfo>('/auth/me', { redirectOn401: false }))
}
