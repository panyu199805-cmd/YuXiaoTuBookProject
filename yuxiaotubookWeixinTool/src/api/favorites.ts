import { fetchData, get } from './client'
import type { BookListItem } from '@/types/book'

const silent401 = { redirectOn401: false } as const

export function listFavorites() {
  return fetchData(get<BookListItem[]>('/favorites', silent401))
}

export function listHistory() {
  return fetchData(get<BookListItem[]>('/history', silent401))
}
