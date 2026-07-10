export interface BookCategory {
  id: number
  name: string
  slug?: string
}

export interface BookListItem {
  id: number
  title: string
  author: string
  cover: string
  highlight?: string
  category?: BookCategory | null
  price?: number
  has_video?: boolean
  view_count?: number
}

export interface BookDetail extends BookListItem {
  stock?: number
  summary?: string
  target_audience?: string
  status?: string
  ebook_title?: string
  ebook_content?: string
  video?: {
    duration?: number
    cover?: string
    intro?: string
  }
}

export interface PlayAuth {
  video_url: string
  poster?: string
  duration?: number
  full_access: boolean
  max_duration?: number | null
  is_vip?: boolean
}

export interface BookQuery {
  page?: number
  page_size?: number
  sort?: 'hot' | 'new'
  keyword?: string
  category_id?: number | string
}
