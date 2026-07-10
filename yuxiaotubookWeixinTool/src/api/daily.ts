import { fetchData, get, post } from './client'
import type { DailyItem } from '@/types/daily'
import type { PageResult } from '@/types/api'

export function getTodayDaily() {
  return fetchData(get<DailyItem | null>('/daily/today', false))
}

export function listDaily(page = 1, pageSize = 10) {
  return fetchData(
    get<PageResult<DailyItem>>(`/daily/list?page=${page}&page_size=${pageSize}`, false),
  )
}

export function likeDaily(id: number) {
  return fetchData(post<{ like_count: number }>(`/daily/${id}/like`, undefined, false))
}
