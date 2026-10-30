/** 构建标识：Console 出现 [YXT-MP] 即表示已加载最新 client */
export const MP_CLIENT_VERSION = '20260711-17'

export const API_BASE =
  import.meta.env.VITE_API_BASE || 'https://www.yuxiaotubook.com/api/v1'

export const MEDIA_ORIGIN =
  import.meta.env.VITE_MEDIA_ORIGIN || 'https://www.yuxiaotubook.com'

/** 订单/会员由 Java trade-service 提供；生产环境经 Nginx 与 Python 同域 */
function resolveTradeApiBase(): string {
  if (import.meta.env.VITE_TRADE_API_BASE) {
    return import.meta.env.VITE_TRADE_API_BASE
  }
  if (/yuxiaotubook\.com/i.test(API_BASE)) {
    return API_BASE
  }
  try {
    const url = new URL(API_BASE)
    if (url.port === '8443') {
      url.port = '8444'
    } else {
      url.port = '8081'
    }
    return url.toString().replace(/\/$/, '')
  } catch {
    return 'http://127.0.0.1:8081/api/v1'
  }
}

export const TRADE_API_BASE = resolveTradeApiBase()
