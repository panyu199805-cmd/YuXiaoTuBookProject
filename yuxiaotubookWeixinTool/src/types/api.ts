export interface ApiResponse<T = unknown> {
  code: number
  msg: string
  data: T
}

export interface PageResult<T> {
  list: T[]
  total: number
  page: number
  page_size: number
}
