import { fetchData, get } from './client'
import type { BookCategory } from '@/types/book'

export interface SiteConfig {
  bg_type?: string
  bg_url?: string | null
  bg_videos?: string[]
  bg_music?: string | null
  white_noise?: string | null
  music_enabled?: boolean
  bg_enabled?: boolean
  promo_title?: string
  daily_sentence?: string
}

export function getSiteConfig() {
  return fetchData(get<SiteConfig>('/site/config', false))
}

export function getCategories() {
  return fetchData(get<BookCategory[]>('/categories', false))
}
