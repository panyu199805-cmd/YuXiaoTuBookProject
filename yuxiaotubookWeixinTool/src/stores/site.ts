import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { getSiteConfig, type SiteConfig } from '@/api/site'
import { resolveMediaUrl } from '@/utils/media'
import { protectVideoUrl } from '@/utils/video'

function isVideoUrl(url?: string | null) {
  if (!url) return false
  const path = url.split('?', 1)[0]
  if (/^\/media\/v\/(homePage|bookReview)\//i.test(path)) return true
  return /\.(mp4|webm)(\?.*)?$/i.test(url)
}

function parseBgVideos(config: SiteConfig | null): string[] {
  if (!config) return []
  const list = config.bg_videos
  if (Array.isArray(list) && list.length) {
    return list.filter((item) => typeof item === 'string' && isVideoUrl(item))
  }
  const single = config.bg_url
  return typeof single === 'string' && isVideoUrl(single) ? [single] : []
}

export const useSiteStore = defineStore('site', () => {
  const config = ref<SiteConfig | null>(null)
  const loaded = ref(false)
  const loading = ref(false)

  const bgVideos = computed(() =>
    parseBgVideos(config.value).map((url) =>
      resolveMediaUrl(protectVideoUrl(url)),
    ),
  )

  const bgImage = computed(() => {
    const url = config.value?.bg_url
    if (!url || isVideoUrl(url)) return ''
    return resolveMediaUrl(url)
  })

  const useVideoBg = computed(
    () => Boolean(config.value?.bg_enabled && parseBgVideos(config.value).length > 0),
  )

  const promoTitle = computed(() => config.value?.promo_title || '宇小兔读书')
  const dailySentence = computed(() => config.value?.daily_sentence || '')

  async function fetchConfig(force = false) {
    if (loaded.value && !force) return config.value
    if (loading.value) return config.value
    loading.value = true
    try {
      config.value = await getSiteConfig()
      loaded.value = true
    } catch {
      loaded.value = true
    } finally {
      loading.value = false
    }
    return config.value
  }

  return {
    config,
    loaded,
    loading,
    bgVideos,
    bgImage,
    useVideoBg,
    promoTitle,
    dailySentence,
    fetchConfig,
  }
})
