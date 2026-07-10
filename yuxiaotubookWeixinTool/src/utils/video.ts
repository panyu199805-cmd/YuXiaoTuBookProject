/** 将直链 mp4 转为无扩展名的流媒体地址 */
export function protectVideoUrl(url?: string | null): string {
  if (!url) return ''
  const [path, query = ''] = url.split('?', 2)
  const match = path.match(/^\/uploads\/(homePage|bookReview)\/(.+)\.(mp4|webm)$/i)
  if (!match) return url
  const category = match[1]
  const basename = decodeURIComponent(match[2])
  const protectedPath = `/media/v/${category}/${encodeURIComponent(basename)}`
  return query ? `${protectedPath}?${query}` : protectedPath
}
