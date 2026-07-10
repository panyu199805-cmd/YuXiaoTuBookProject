import { defineStore } from 'pinia'
import { request } from '@/api/client'
import { resolveMediaUrl } from '@/utils/media'
import { protectVideoUrl } from '@/utils/video'

function isVideoUrl(url?: string | null) {
  if (!url) return false
  const path = url.split('?', 1)[0]
  if (/^\/media\/v\/(homePage|bookReview)\//i.test(path)) return true
  return /\.(mp4|webm)(\?.*)?$/i.test(url)
}

function parseBgVideos(config: Record<string, unknown> | null): string[] {
  if (!config) return []
  const list = config.bg_videos
  if (Array.isArray(list) && list.length) {
    return list.filter((item): item is string => typeof item === 'string' && isVideoUrl(item))
  }
  const single = config.bg_url
  return typeof single === 'string' && isVideoUrl(single) ? [single] : []
}

export const useSiteStore = defineStore('site', {
  state: () => ({
    config: null as Record<string, unknown> | null,
    loaded: false,
    loading: false,
  }),
  getters: {
    bgVideos: (state): string[] =>
      parseBgVideos(state.config).map((url) => protectVideoUrl(resolveMediaUrl(url))),
    useVideoBg: (state): boolean =>
      Boolean(state.config?.bg_enabled && parseBgVideos(state.config).length > 0),
  },
  actions: {
    async fetchConfig(force = false) {
      if (this.loaded && !force) return this.config
      if (this.loading) return this.config
      this.loading = true
      try {
        const res = await request<Record<string, unknown>>({ url: '/site/config' })
        if (res.code === 200 && res.data) {
          this.config = res.data
        }
        this.loaded = true
        return this.config
      } catch {
        this.loaded = true
        return this.config
      } finally {
        this.loading = false
      }
    },
  },
})
