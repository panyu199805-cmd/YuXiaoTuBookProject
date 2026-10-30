import { API_BASE, MP_CLIENT_VERSION, TRADE_API_BASE } from '@/config/env'
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

function parseResponseBody<T>(raw: unknown): ApiResponse<T> {
  if (raw == null) return {} as ApiResponse<T>
  if (typeof raw === 'string') {
    const text = raw.trim()
    if (!text) return {} as ApiResponse<T>
    try {
      return JSON.parse(text) as ApiResponse<T>
    } catch {
      return { code: -1, msg: text.slice(0, 120), data: null } as ApiResponse<T>
    }
  }
  if (typeof ArrayBuffer !== 'undefined' && raw instanceof ArrayBuffer) {
    try {
      const text = new TextDecoder('utf-8').decode(raw).trim()
      if (!text) return {} as ApiResponse<T>
      return JSON.parse(text) as ApiResponse<T>
    } catch {
      return { code: -1, msg: 'ArrayBuffer 响应无法解析', data: null } as ApiResponse<T>
    }
  }
  return raw as ApiResponse<T>
}

/** 兼容后端返回 number / string 类型的 code */
function isOkCode(code: unknown): boolean {
  if (code === 200 || code === '200') return true
  const n = Number(code)
  return Number.isFinite(n) && n === 200
}

function localDevHint(isTimeout: boolean) {
  if (API_BASE.includes('127.0.0.1')) {
    return '微信禁止 127.0.0.1，请运行 start-mp-simulator.bat 使用局域网 IP'
  }
  if (/192\.168\.|10\.\d+\.|^http:\/\//.test(API_BASE)) {
    return isTimeout
      ? '请确认 Python :8000 / Java :8081 已启动，且详情里已勾选不校验合法域名'
      : '请确认本地后端已启动（start-mp-simulator.bat）'
  }
  if (API_BASE.startsWith('https://') && /:\8443/.test(API_BASE)) {
    return isTimeout
      ? '真机调试请用 start-mp-real-device.bat（HTTPS）'
      : '请先运行 dev-https-proxy.ps1'
  }
  return isTimeout
    ? '生产 API 超时，真机调试请用 build-mp-local.bat 构建本地包'
    : '生产 API 不可达，真机调试请用 build-mp-local.bat'
}

function formatHttpError(statusCode: number, raw: unknown): string {
  const body = raw as { detail?: unknown; msg?: string }
  if (statusCode === 422 && Array.isArray(body?.detail)) {
    const lines = body.detail.map((item: { loc?: unknown[]; type?: string; msg?: string }) => {
      const field = Array.isArray(item.loc) ? String(item.loc[item.loc.length - 1] ?? '') : ''
      if (item.type === 'string_too_short' && field === 'username') return '用户名至少 4 个字符'
      if (item.type === 'string_too_short' && field === 'password') return '密码至少 8 位'
      if (item.type === 'string_too_long' && field === 'username') return '用户名最多 20 个字符'
      if (item.type === 'json_invalid') return '请求格式错误，请重新编译小程序'
      if (field && item.msg) return `${field}: ${item.msg}`
      return item.msg || '参数校验失败'
    })
    return lines.filter(Boolean).join('；') || '参数校验失败'
  }
  if (body?.msg) return body.msg
  return `HTTP ${statusCode}`
}

function serializeRequestData(method: string, data?: Record<string, unknown>) {
  if (data == null || method === 'GET') return data
  return JSON.stringify(data)
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
  const header: Record<string, string> = {}
  if (method !== 'GET') {
    header['Content-Type'] = 'application/json'
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
      data: serializeRequestData(method, data),
      header,
      dataType: 'json',
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
        if (res.statusCode && res.statusCode >= 400) {
          const hint =
            res.statusCode === 503 && API_BASE.startsWith('http://')
              ? 'HTTP 被拦截：详情→本地设置→勾选不校验合法域名，或改用 start-mp-real-device.bat'
              : formatHttpError(res.statusCode, res.data)
          console.error('[API]', method, fullUrl, hint, res.data)
          uni.showToast({ title: hint, icon: 'none', duration: 4000 })
          reject(new Error(hint))
          return
        }
        const body = parseResponseBody<T>(res.data)
        if (res.statusCode === 401 || body.code === 401) {
          if (auth) clearAuth()
          if (redirectOn401) redirectToLogin()
          reject(new Error(body.msg || '未登录'))
          return
        }
        if (!isOkCode(body.code)) {
          const msg =
            body.msg ||
            (body.code == null
              ? `[${MP_CLIENT_VERSION}] 非 JSON 响应 ${fullUrl}，请清缓存后运行 build-mp-local.bat`
              : `[${MP_CLIENT_VERSION}] 业务错误 code=${String(body.code)} ${fullUrl}`)
          console.error('[API]', MP_CLIENT_VERSION, method, fullUrl, 'biz error', body.code, res.data)
          uni.showToast({ title: msg, icon: 'none', duration: 4000 })
          reject(new Error(msg))
          return
        }
        resolve(body)
      },
      fail: (err) => {
        const errMsg = err?.errMsg || String(err)
        const isTimeout = /timeout/i.test(errMsg)
        const isTunnel = /TUNNEL_CONNECTION_FAILED|errcode:-111/i.test(errMsg)
        const isRefused = /CONNECTION_REFUSED|errcode:-102/i.test(errMsg)
        const isCert = /CERT_AUTHORITY_INVALID|errcode:-202/i.test(errMsg)
        let hint = localDevHint(isTimeout)
        if (isCert) {
          hint = 'HTTPS 证书错误：模拟器请用 start-mp-simulator.bat（HTTP 局域网，无需证书）'
        } else if (isTunnel) {
          hint = '代理冲突(-111)：运行 fix-mp-network.bat 并重启微信开发者工具'
        } else if (isRefused) {
          hint = '连接被拒：确认后端 :8000 已启动，并运行 start-mp-simulator.bat 重新构建'
        }
        uni.showToast({
          title: isTimeout ? `请求超时：${hint}` : isCert || isTunnel || isRefused ? hint : `网络异常：${hint}`,
          icon: 'none',
          duration: 5000,
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
