import { request } from '@/api/client'

export type AiContentType =
  | 'book_summary'
  | 'book_highlight'
  | 'video_explain'
  | 'video_intro'
  | 'daily_sentence'
  | 'daily_intro'
  | 'reading_note'

export interface AiContentTypeOption {
  value: AiContentType
  label: string
  target_field: string
}

export interface AiRuntimeConfig {
  configured: boolean
  mock_enabled: boolean
  mode: 'live' | 'mock' | 'disabled'
  base_url: string | null
  model: string | null
  content_types: AiContentTypeOption[]
}

export interface AiContentItem {
  id: number
  task_id: number
  book_id: number
  book_title: string | null
  book_author: string | null
  book_cover: string | null
  content_type: AiContentType
  content_type_label: string
  target_field: string
  source_text: string | null
  generated_text: string | null
  edited_text: string | null
  final_text: string | null
  status: string
  error_message: string | null
  applied_at: string | null
  created_at: string | null
  updated_at: string | null
}

export interface AiContentTask {
  id: number
  operator_id: number
  status: string
  content_types: string[]
  book_ids: number[]
  tone: string
  length: string
  extra_prompt: string | null
  write_mode: string
  provider_mode: string
  model_name: string | null
  error_message: string | null
  created_at: string | null
  finished_at: string | null
  items: AiContentItem[]
}

export interface AiGeneratePayload {
  book_ids: number[]
  content_types: AiContentType[]
  tone: string
  length: string
  extra_prompt?: string
  write_mode: 'empty_only' | 'overwrite'
}

export function fetchAiConfig() {
  return request<AiRuntimeConfig>({ url: '/admin/ai/config' })
}

export function generateAiContent(data: AiGeneratePayload) {
  return request<AiContentTask>({
    url: '/admin/ai/generate',
    method: 'POST',
    data,
    timeout: 180000,
  })
}

export function fetchAiTasks(limit = 20) {
  return request<AiContentTask[]>({ url: '/admin/ai/tasks', params: { limit } })
}

export function fetchAiTask(taskId: number) {
  return request<AiContentTask>({ url: `/admin/ai/tasks/${taskId}` })
}

export function updateAiItem(itemId: number, text: string) {
  return request<AiContentItem>({
    url: `/admin/ai/items/${itemId}`,
    method: 'PUT',
    data: { text },
  })
}

export function acceptAiItem(
  itemId: number,
  data: { text?: string; write_mode?: string; publish_date?: string } = {},
) {
  return request<AiContentItem>({
    url: `/admin/ai/items/${itemId}/accept`,
    method: 'POST',
    data,
  })
}

export function discardAiItem(itemId: number) {
  return request<AiContentItem>({
    url: `/admin/ai/items/${itemId}/discard`,
    method: 'POST',
  })
}
