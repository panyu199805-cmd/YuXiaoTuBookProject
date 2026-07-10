import { fetchData, tradeGet, tradePost } from './client'
import type { MemberPackage, MemberStatus, OrderInfo } from '@/types/user'

export function getMemberPackages() {
  return fetchData(tradeGet<MemberPackage[]>('/member/packages', false))
}

export function getMemberStatus() {
  return fetchData(tradeGet<MemberStatus>('/member/status', { redirectOn401: false }))
}

export function subscribeMember(packageId: number) {
  return fetchData(tradePost<{ id: number }>('/member/subscribe', { package_id: packageId }))
}

export function mockPayMemberOrder(orderId: number) {
  return fetchData(tradePost<Record<string, unknown>>(`/member/orders/${orderId}/mock-pay`))
}

export function listOrders() {
  return fetchData(tradeGet<OrderInfo[]>('/orders', { redirectOn401: false }))
}

export function createOrder(payload: {
  book_id: number
  quantity: number
  receiver_name: string
  receiver_phone: string
  receiver_address: string
}) {
  return fetchData(tradePost<{ id: number }>('/orders', payload as unknown as Record<string, unknown>))
}

export function mockPayOrder(orderId: number) {
  return fetchData(tradePost<OrderInfo>(`/orders/${orderId}/mock-pay`))
}
