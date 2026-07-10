import { fetchData, get, put } from './client'
import type { OrderInfo, UserPreferences } from '@/types/user'

export function getPreferences() {
  return fetchData(get<UserPreferences>('/user/preferences'))
}

export function savePreferences(data: UserPreferences) {
  return fetchData(put<UserPreferences>('/user/preferences', data as unknown as Record<string, unknown>))
}

export function getShippingOrders() {
  return fetchData(get<OrderInfo[]>('/user/orders/shipping'))
}
