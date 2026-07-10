import { fetchData, get } from './client'
import type { BookListItem } from '@/types/book'
import type { PageResult } from '@/types/api'

export function getFeatured() {
  return fetchData(get<BookListItem | null>('/home/featured', false))
}

export function getHotBooks(page = 1, pageSize = 12) {
  return fetchData(
    get<PageResult<BookListItem>>(`/home/hot-books?page=${page}&page_size=${pageSize}`, false),
  )
}
