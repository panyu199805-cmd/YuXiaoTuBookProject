import { API_BASE, TRADE_API_BASE } from '@/config/env'
import type { ApiResponse } from '@/types/api'
import { clearAuth, getToken } from '@/utils/storage'

export interface RequestMeta {
  auth?: boolean
  base?: string
  redirectOn401?: boolean
}

interface RequestOptions extends RequestMeta {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: Record<string, unknown>
}

function normalizeMeta(meta?: boolean | RequestMeta, defaultAuth = true): Required<RequestMeta> {
  const opts = typeof meta === 'boolean' ? { auth: meta } : meta || {}
  return {
    auth: opts.auth ?? defaultAuth,
    base: opts.base ?? API_BASE,
    redirectOn401: opts.redirectOn401 ?? true,
  }
}

function redirectToLogin() {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  const route = current?.route ? `/${current.route}` : '/pages/index/index'
  uni.navigateTo({
    url: `/pages/auth/login?redirect=${encodeURIComponent(route)}`,
  })
}

export function request<T>(opts: RequestOptions): Promise<ApiResponse<T>> {
  const {
    url,
    method = 'GET',
    data,
    auth = true,
    base = API_BASE,
    redirectOn401 = true,
  } = opts
  const header: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (auth) {
    const token = getToken()
    if (token) header.Authorization = `Bearer ${token}`
  }

  const fullUrl = `${base}${url}`

  return new Promise((resolve, reject) => {
    uni.request({
      url: fullUrl,
      method,
      data,
      header,
      timeout: 30000,
      success: (res) => {
        if (res.statusCode === 404) {
          const tradeHint =
            base === API_BASE && (url.startsWith('/orders') || url.startsWith('/member'))
              ? '订单/会员应走 Java :8081，请确认 trade 服务已启动'
              : '接口不存在'
          console.error('[API]', method, fullUrl, 'HTTP 404', tradeHint)
          reject(new Error(tradeHint))
          return
        }
        const body = (res.data || {}) as ApiResponse<T>
        if (res.statusCode === 401 || body.code === 401) {
          if (auth) clearAuth()
          if (redirectOn401) redirectToLogin()
          reject(new Error(body.msg || '未登录'))
          return
        }
        if (body.code !== 200) {
          uni.showToast({ title: body.msg || '请求失败', icon: 'none' })
          reject(new Error(body.msg || '请求失败'))
          return
        }
        resolve(body)
      },
      fail: (err) => {
        const errMsg = err?.errMsg || String(err)
        const isTimeout = /timeout/i.test(errMsg)
        const hint =
          API_BASE.includes('127.0.0.1') || API_BASE.includes('192.168')
            ? isTimeout
              ? '微信工具无法访问局域网 API，请运行 scripts\\check-mp-api.ps1 排查防火墙'
              : '请确认本地后端已启动（开发文档\\本地运行.ps1）'
            : '生产 API 不可达，可改用 build-mp-local.bat 联调本地后端'
        uni.showToast({
          title: isTimeout ? `请求超时：${hint}` : `网络异常：${hint}`,
          icon: 'none',
          duration: 4000,
        })
        console.error('[API]', method, fullUrl, errMsg)
        reject(new Error(errMsg || '网络异常'))
      },
    })
  })
}

export function get<T>(url: string, meta?: boolean | RequestMeta) {
  const { auth, base, redirectOn401 } = normalizeMeta(meta)
  return request<T>({ url, method: 'GET', auth, base, redirectOn401 })
}

export function post<T>(url: string, data?: Record<string, unknown>, meta?: boolean | RequestMeta) {
  const { auth, base, redirectOn401 } = normalizeMeta(meta)
  return request<T>({ url, method: 'POST', data, auth, base, redirectOn401 })
}

export function put<T>(url: string, data?: Record<string, unknown>, meta?: boolean | RequestMeta) {
  const { auth, base, redirectOn401 } = normalizeMeta(meta)
  return request<T>({ url, method: 'PUT', data, auth, base, redirectOn401 })
}

export function del<T>(url: string, meta?: boolean | RequestMeta) {
  const { auth, base, redirectOn401 } = normalizeMeta(meta)
  return request<T>({ url, method: 'DELETE', auth, base, redirectOn401 })
}

/** Java trade-service：订单、会员 */
export function tradeGet<T>(url: string, meta?: boolean | RequestMeta) {
  const { auth, redirectOn401 } = normalizeMeta(meta)
  return get<T>(url, { auth, base: TRADE_API_BASE, redirectOn401 })
}

export function tradePost<T>(
  url: string,
  data?: Record<string, unknown>,
  meta?: boolean | RequestMeta,
) {
  const { auth, redirectOn401 } = normalizeMeta(meta)
  return post<T>(url, data, { auth, base: TRADE_API_BASE, redirectOn401 })
}

/** 解包 data，简化页面调用 */
export async function fetchData<T>(promise: Promise<ApiResponse<T>>): Promise<T> {
  const res = await promise
  return res.data
}
