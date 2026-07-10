/**
 * 微信小程序基础库 3.15+ 要求图片/视频使用 HTTPS。
 * 本地开发：HTTP URL 先 downloadFile 到临时路径再展示。
 */
const cache = new Map<string, string>()

export function isHttpUrl(url?: string | null): boolean {
  return !!url && url.startsWith('http://')
}

export async function toMpSafeMediaUrl(url?: string | null): Promise<string> {
  if (!url) return ''
  if (!isHttpUrl(url)) return url

  const cached = cache.get(url)
  if (cached) return cached

  return new Promise((resolve) => {
    uni.downloadFile({
      url,
      timeout: 15000,
      success: (res) => {
        if (res.statusCode === 200 && res.tempFilePath) {
          cache.set(url, res.tempFilePath)
          resolve(res.tempFilePath)
        } else {
          console.warn('[media] download non-200', url, res.statusCode)
          resolve('')
        }
      },
      fail: (err) => {
        console.warn('[media] download fail', url, err?.errMsg || err)
        resolve('')
      },
    })
  })
}

export function clearMediaCache() {
  cache.clear()
}
