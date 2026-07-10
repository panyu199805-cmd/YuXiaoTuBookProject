import { MEDIA_ORIGIN } from '@/config/env'

const BOOK_COVER_BY_ID: Record<number, string> = {
  1: '/placeholders/books/bei-tao-yan-de-yong-qi.svg',
  2: '/placeholders/books/xiao-wang-zi.svg',
  3: '/placeholders/books/fei-bao-li-gou-tong.svg',
  4: '/placeholders/books/yuan-ze.svg',
  5: '/placeholders/books/huo-zhe.svg',
  6: '/placeholders/books/zheng-mian-guan-jiao.svg',
  7: '/placeholders/books/xin-liu.svg',
  8: '/placeholders/books/jie-you-za-huo-dian.svg',
  9: '/placeholders/books/shen-du-gong-zuo.svg',
  10: '/placeholders/books/wo-men-sa.svg',
}

export function placeholderCover(id = 1): string {
  return resolveMediaUrl(BOOK_COVER_BY_ID[id] || BOOK_COVER_BY_ID[1])
}

/** 解析 API 返回的封面/媒体路径为完整 HTTPS URL */
export function resolveMediaUrl(url?: string | null, id = 1): string {
  if (!url) return placeholderCover(id)
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
    return url
  }
  const base = MEDIA_ORIGIN.replace(/\/$/, '')
  const path = url.startsWith('/') ? url : `/${url}`
  return `${base}${path}`
}
