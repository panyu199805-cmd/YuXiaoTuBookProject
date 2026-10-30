import { fetchData, get, post } from './client'
import type { BookDetail, BookListItem, BookQuery, PlayAuth } from '@/types/book'
import type { PageResult } from '@/types/api'

function buildQuery(params: BookQuery) {
  return Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== '')
    .map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`)
    .join('&')
}

export function listBooks(params: BookQuery = {}) {
  const qs = buildQuery(params)
  return fetchData(get<PageResult<BookListItem>>(`/books?${qs}`, false))
}

export function getBook(id: number) {
  return fetchData(get<BookDetail>(`/books/${id}`, false))
}

export function getPlayAuth(id: number) {
  return fetchData(get<PlayAuth>(`/books/${id}/play-auth`, { auth: true, redirectOn401: false }))
}

export function getSimilar(id: number) {
  return fetchData(get<BookListItem[]>(`/books/${id}/similar`, false))
}

export function addFavorite(bookId: number) {
  return fetchData(post<null>('/favorites', { book_id: bookId }))
}

export function reportPlay(id: number, position: number) {
  return fetchData(post<null>(`/books/${id}/play-report`, { position }, false))
}
