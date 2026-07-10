import type { BookListItem } from './book'

export interface DailyItem {
  id: number
  book_id: number
  daily_sentence: string
  daily_intro?: string
  publish_date: string
  is_top?: boolean
  like_count: number
  book?: BookListItem | null
}
