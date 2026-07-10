export interface UserInfo {
  id: number
  username: string
  nickname: string
  role?: string
  avatar?: string
  is_vip?: boolean
  vip_expire_time?: string | null
}

export interface UserPreferences {
  category_ids: number[]
  scene_tags: string[]
  bio: string
}

export interface MemberStatus {
  is_vip: boolean
  expire_time?: string | null
  package_id?: number | null
  package_name?: string | null
}

export interface MemberPackage {
  id: number
  package_name: string
  price: number
  valid_day: number
  rights: string[] | string
}

export interface OrderItem {
  book_id?: number
  book_title?: string
  quantity?: number
  price?: number
}

export interface OrderInfo {
  id: number
  order_no: string
  status: string
  status_label?: string
  total_amount: number
  items?: OrderItem[]
  receiver_name?: string
  receiver_phone?: string
  receiver_address?: string
  ship_company?: string
  ship_tracking_no?: string
  shipped_at?: string | null
}
