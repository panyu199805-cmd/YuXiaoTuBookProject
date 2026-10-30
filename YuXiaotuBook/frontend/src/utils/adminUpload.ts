import http from '@/api/client'

export interface AdminUploadResult {
  url: string
  media_type?: string
}

/** 管理后台统一文件上传（POST /admin/upload） */
export async function uploadAdminFile(file: File): Promise<AdminUploadResult> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await http.post('/admin/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  const body = res.data
  if (body.code === 200 && body.data?.url) {
    return body.data as AdminUploadResult
  }
  throw new Error(body.msg || 'upload failed')
}

/** 上传首页背景视频到 uploads/homePage */
export async function uploadHomePageVideo(file: File): Promise<AdminUploadResult> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await http.post('/admin/home-page-videos/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  const body = res.data
  if (body.code === 200 && body.data?.url) {
    return body.data as AdminUploadResult
  }
  throw new Error(body.msg || 'upload failed')
}

/** 删除 homePage 目录中的背景视频 */
export async function deleteHomePageVideo(url: string): Promise<void> {
  const res = await http.delete('/admin/home-page-videos', { params: { url } })
  const body = res.data
  if (body.code !== 200) {
    throw new Error(body.msg || 'delete failed')
  }
}

/** 上传图书解读视频到 uploads/bookReview */
export async function uploadBookReviewVideo(file: File): Promise<AdminUploadResult> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await http.post('/admin/book-review-videos/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  const body = res.data
  if (body.code === 200 && body.data?.url) {
    return body.data as AdminUploadResult
  }
  throw new Error(body.msg || 'upload failed')
}

/** 删除 bookReview 目录中的解读视频文件 */
export async function deleteBookReviewVideo(url: string): Promise<void> {
  const res = await http.delete('/admin/book-review-videos', { params: { url } })
  const body = res.data
  if (body.code !== 200) {
    throw new Error(body.msg || 'delete failed')
  }
}
