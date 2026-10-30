import axios, { type AxiosRequestConfig } from 'axios'

export interface ApiResponse<T = unknown> {
  code: number
  msg: string
  data: T
}

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
    const body = err.response?.data
    const payload =
      body && typeof body.code === 'number'
        ? body
        : body?.detail && typeof body.detail.code === 'number'
          ? body.detail
          : null
    if (payload) {
      return Promise.resolve({ data: payload })
    }
    return Promise.reject(err)
  }
)

export async function request<T>(config: AxiosRequestConfig): Promise<ApiResponse<T>> {
  const res = await http.request<ApiResponse<T>>({
    timeout: 30000,
    ...config,
  })
  return res.data
}

export default http
