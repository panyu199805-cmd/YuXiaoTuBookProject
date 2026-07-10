<script setup lang="ts">
import { computed, nextTick, onActivated, onDeactivated, onMounted, onUnmounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useHead } from '@unhead/vue'
import BookCard from '@/components/BookCard.vue'
import HeroSearchBox from '@/components/HeroSearchBox.vue'
import HeroVideoLayer from '@/components/HeroVideoLayer.vue'
import { request } from '@/api/client'
import { inlineCoverFallback, placeholderCover, resolveMediaUrl } from '@/utils/media'
import { useSiteStore } from '@/stores/site'

defineOptions({ name: 'Home' })

useHead({ title: '宇小兔每日读书 - 首页' })

const siteStore = useSiteStore()
const { config, bgVideos, useVideoBg: storeUseVideoBg } = storeToRefs(siteStore)

const featured = ref<any>(null)
const hotBooks = ref<any[]>([])
const categories = ref<any[]>([])
const videoFailed = ref(false)
const featuredCover = ref('')
const videoLayerRefs = ref<(InstanceType<typeof HeroVideoLayer> | null)[]>([null, null])
const layerSrc = ref<[string, string]>(['', ''])
const activeLayer = ref(0)
const currentVideoIndex = ref(0)
const isTransitioning = ref(false)

const CROSSFADE_MS = 1200
const PRELOAD_DELAY_MS = 1500
const CANPLAY_TIMEOUT_MS = 12000
let crossfadeTimer: ReturnType<typeof setTimeout> | null = null
let preloadTimer: ReturnType<typeof setTimeout> | null = null
let advanceToken = 0

function bumpAdvanceToken() {
  advanceToken += 1
  return advanceToken
}

function setVideoLayerRef(index: number, el: unknown) {
  videoLayerRefs.value[index] = el as InstanceType<typeof HeroVideoLayer> | null
}

function getVideoLayer(index: number) {
  return videoLayerRefs.value[index]?.el ?? null
}

function getActiveVideoEl() {
  return getVideoLayer(activeLayer.value)
}

function onFeaturedCoverError() {
  if (!featured.value) return
  const fallback = placeholderCover(featured.value.id)
  featuredCover.value =
    featuredCover.value === fallback
      ? inlineCoverFallback(featured.value.title, featured.value.id)
      : fallback
}

const useVideoBg = computed(() => storeUseVideoBg.value && !videoFailed.value)

const heroImageStyle = computed(() => {
  if (useVideoBg.value) return {}
  const url = config.value?.bg_url as string | undefined
  const resolved = resolveMediaUrl(url)
  if (!resolved || /\.(mp4|webm)(\?.*)?$/i.test(resolved)) return {}
  return { backgroundImage: `url(${resolved})` }
})

const showHeroFallback = computed(() => {
  if (useVideoBg.value) return false
  if (bgVideos.value.length) return false
  const url = config.value?.bg_url as string | undefined
  if (!url) return true
  if (videoFailed.value && /\.(mp4|webm)(\?.*)?$/i.test(url)) return true
  return false
})

function onVideoError() {
  videoFailed.value = true
}

const showVideoNav = computed(() => useVideoBg.value && bgVideos.value.length >= 1)
const canSwitchVideo = computed(() => bgVideos.value.length > 1)

const navArrowsVisible = ref(false)
const NAV_VISIBLE_MS = 3000
let navHideTimer: ReturnType<typeof setTimeout> | null = null

function clearNavHideTimer() {
  if (navHideTimer) {
    clearTimeout(navHideTimer)
    navHideTimer = null
  }
}

function revealNavArrows() {
  navArrowsVisible.value = true
  clearNavHideTimer()
  navHideTimer = setTimeout(() => {
    navArrowsVisible.value = false
    navHideTimer = null
  }, NAV_VISIBLE_MS)
}

function onNavZoneEnter() {
  revealNavArrows()
}

function waitCanPlay(video: HTMLVideoElement, timeoutMs = CANPLAY_TIMEOUT_MS): Promise<void> {
  if (video.readyState >= HTMLMediaElement.HAVE_FUTURE_DATA) return Promise.resolve()
  return new Promise((resolve) => {
    const timer = window.setTimeout(() => resolve(), timeoutMs)
    const done = () => {
      window.clearTimeout(timer)
      resolve()
    }
    video.addEventListener('canplay', done, { once: true })
    video.addEventListener('error', done, { once: true })
    if (video.readyState === HTMLMediaElement.HAVE_NOTHING) {
      video.load()
    }
  })
}

function prepareVideoLayer(layer: number) {
  videoLayerRefs.value[layer]?.prepareBuffer?.()
}

function setLayerSrc(layer: 0 | 1, url: string) {
  const next: [string, string] = [layerSrc.value[0], layerSrc.value[1]]
  next[layer] = url
  layerSrc.value = next
}

function advanceToNextVideo() {
  const list = bgVideos.value
  if (list.length <= 1) {
    const el = getActiveVideoEl()
    if (el) {
      el.currentTime = 0
      void el.play().catch(() => {})
    }
    return
  }

  const nextIndex = (currentVideoIndex.value + 1) % list.length
  void goToVideo(nextIndex)
}

function clearPreloadTimer() {
  if (preloadTimer) {
    clearTimeout(preloadTimer)
    preloadTimer = null
  }
}

function preloadAdjacentVideo() {
  const list = bgVideos.value
  if (list.length <= 1) return
  clearPreloadTimer()
  preloadTimer = setTimeout(() => {
    preloadTimer = null
    const nextIdx = (currentVideoIndex.value + 1) % list.length
    const backLayer = (1 - activeLayer.value) as 0 | 1
    const nextUrl = list[nextIdx]
    if (layerSrc.value[backLayer] !== nextUrl) {
      setLayerSrc(backLayer, nextUrl)
    }
  }, PRELOAD_DELAY_MS)
}

function resumeHeroVideo() {
  const el = getActiveVideoEl()
  if (!el || !useVideoBg.value) return
  void el.play().catch(() => {})
}

function onHeroVideoLoaded(layer: number) {
  if (layer !== activeLayer.value) return
  resumeHeroVideo()
  preloadAdjacentVideo()
}

function resetVideoLayers() {
  if (crossfadeTimer) {
    clearTimeout(crossfadeTimer)
    crossfadeTimer = null
  }
  bumpAdvanceToken()
  isTransitioning.value = false
  currentVideoIndex.value = 0
  activeLayer.value = 0
  const list = bgVideos.value
  layerSrc.value = list.length ? [list[0], ''] : ['', '']
}

async function goToVideo(nextIndex: number) {
  const list = bgVideos.value
  if (!list.length || !useVideoBg.value) return

  const normalized = ((nextIndex % list.length) + list.length) % list.length

  if (list.length === 1) {
    const el = getActiveVideoEl()
    if (!el) return
    el.currentTime = 0
    void el.play().catch(() => {})
    return
  }

  if (isTransitioning.value) return
  if (normalized === currentVideoIndex.value) return

  isTransitioning.value = true
  const token = bumpAdvanceToken()
  const prevLayer = activeLayer.value
  const backLayer = (1 - prevLayer) as 0 | 1
  setLayerSrc(backLayer, list[normalized])

  await nextTick()
  prepareVideoLayer(backLayer)
  await nextTick()
  const backEl = getVideoLayer(backLayer)
  if (!backEl) {
    isTransitioning.value = false
    return
  }

  if (backEl.readyState < HTMLMediaElement.HAVE_FUTURE_DATA) {
    await waitCanPlay(backEl)
  }
  if (token !== advanceToken) {
    isTransitioning.value = false
    return
  }

  backEl.currentTime = 0
  try {
    await backEl.play()
  } catch {
    /* autoplay may fail briefly; still switch layer */
  }
  if (token !== advanceToken) {
    isTransitioning.value = false
    return
  }

  activeLayer.value = backLayer
  currentVideoIndex.value = normalized
  preloadAdjacentVideo()
  isTransitioning.value = false

  if (crossfadeTimer) clearTimeout(crossfadeTimer)
  crossfadeTimer = setTimeout(() => {
    const prevEl = getVideoLayer(prevLayer)
    if (prevEl) {
      prevEl.pause()
      prevEl.currentTime = 0
    }
    crossfadeTimer = null
  }, CROSSFADE_MS)
}

function switchVideo(delta: number) {
  const list = bgVideos.value
  if (list.length <= 1) return
  revealNavArrows()
  if (crossfadeTimer) {
    clearTimeout(crossfadeTimer)
    crossfadeTimer = null
  }
  isTransitioning.value = false
  void goToVideo(currentVideoIndex.value + delta)
}

function onHeroVideoEnded(layer: number) {
  if (layer !== activeLayer.value || bgVideos.value.length <= 1) return
  if (isTransitioning.value) return
  advanceToNextVideo()
}

watch(
  bgVideos,
  (list) => {
    if (!list.length) {
      layerSrc.value = ['', '']
      return
    }
    resetVideoLayers()
    void nextTick().then(() => resumeHeroVideo())
  },
  { immediate: true },
)

function pauseAllHeroVideos() {
  videoLayerRefs.value.forEach((layer) => {
    layer?.el?.pause()
  })
}

function clearHeroTimers() {
  if (crossfadeTimer) {
    clearTimeout(crossfadeTimer)
    crossfadeTimer = null
  }
  clearPreloadTimer()
  bumpAdvanceToken()
  clearNavHideTimer()
}

onActivated(() => {
  void siteStore.fetchConfig(true)
  resumeHeroVideo()
})

onDeactivated(() => {
  pauseAllHeroVideos()
  clearHeroTimers()
})

async function loadHomeData() {
  await siteStore.fetchConfig(true)
  const [feat, hot, cats] = await Promise.all([
    request<any>({ url: '/home/featured' }),
    request<{ list?: any[]; total?: number }>({ url: '/home/hot-books', params: { page: 1, page_size: 12 } }),
    request<any[]>({ url: '/categories' }),
  ])
  if (feat.code === 200) {
    featured.value = feat.data
    featuredCover.value = resolveMediaUrl(feat.data?.cover, feat.data?.id)
  }
  if (hot.code === 200) hotBooks.value = hot.data?.list || []
  if (cats.code === 200) categories.value = cats.data || []
}

onMounted(loadHomeData)

onUnmounted(() => {
  pauseAllHeroVideos()
  clearHeroTimers()
})

const trustItems = [
  { title: '视频解读', desc: '先看再买，降低选书成本' },
  { title: '精选书单', desc: '分类清晰，热门优先展示' },
  { title: '正版购书', desc: '下单发货流程完整可追踪' },
  { title: '每日共读', desc: '专栏更新，养成阅读习惯' },
]
</script>

<template>
  <section class="hero">
    <template v-if="useVideoBg">
      <HeroVideoLayer
        v-for="layer in 2"
        :key="layer - 1"
        :ref="(el) => setVideoLayerRef(layer - 1, el)"
        :src="layerSrc[layer - 1] || undefined"
        :active="activeLayer === layer - 1"
        :loop="bgVideos.length <= 1"
        @loadeddata="onHeroVideoLoaded(layer - 1)"
        @ended="onHeroVideoEnded(layer - 1)"
        @error="onVideoError"
      />
    </template>
    <div
      v-else
      class="hero-media hero-media--image"
      :class="{ 'hero-media--fallback': showHeroFallback }"
      :style="heroImageStyle"
    />

    <div class="hero-shade" />

    <div v-if="showVideoNav" class="hero-video-nav">
      <div class="hero-nav-zone hero-nav-zone--left" @mouseenter="onNavZoneEnter">
        <button
          type="button"
          class="hero-nav-btn"
          :class="{ 'is-visible': navArrowsVisible, 'is-disabled': !canSwitchVideo }"
          :disabled="!canSwitchVideo"
          aria-label="上一个背景视频"
          @click="switchVideo(-1)"
        >
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M15 6l-6 6 6 6" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </div>

      <span
        v-if="canSwitchVideo"
        class="hero-nav-indicator"
        :class="{ 'is-visible': navArrowsVisible }"
      >
        {{ currentVideoIndex + 1 }} / {{ bgVideos.length }}
      </span>

      <div class="hero-nav-zone hero-nav-zone--right" @mouseenter="onNavZoneEnter">
        <button
          type="button"
          class="hero-nav-btn"
          :class="{ 'is-visible': navArrowsVisible, 'is-disabled': !canSwitchVideo }"
          :disabled="!canSwitchVideo"
          aria-label="下一个背景视频"
          @click="switchVideo(1)"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M9 6l6 6-6 6" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </div>
    </div>

    <div class="hero-inner">
      <h1 class="hero-title">{{ config?.promo_title || '读书视频，宇小兔更懂你' }}</h1>
      <p class="hero-subtitle">
        {{ config?.daily_sentence || '先看懂一本书，再决定买不买' }}
      </p>
      <HeroSearchBox :tags="categories" />
    </div>
  </section>

  <section class="trust-bar">
    <div class="container trust-inner">
      <div v-for="item in trustItems" :key="item.title" class="trust-item">
        <strong>{{ item.title }}</strong>
        <span>{{ item.desc }}</span>
      </div>
    </div>
  </section>

  <div v-if="featured" class="container section">
    <h2 class="section-title">今日主推</h2>
    <router-link :to="`/books/${featured.id}`" class="featured">
      <img :src="featuredCover" :alt="featured.title" @error="onFeaturedCoverError" />
      <div class="featured-body">
        <h3>{{ featured.title }}</h3>
        <p class="author">{{ featured.author }}</p>
        <p v-if="featured.highlight" class="highlight">{{ featured.highlight }}</p>
        <span class="featured-cta">观看解读 →</span>
      </div>
    </router-link>
  </div>

  <div class="container section">
    <h2 class="section-title">分类探索</h2>
    <div class="cats">
      <router-link
        v-for="c in categories"
        :key="c.id"
        :to="`/books?category_id=${c.id}`"
        class="cat-chip"
      >
        {{ c.name }}
      </router-link>
    </div>
  </div>

  <div class="container section">
    <div class="section-head">
      <h2 class="section-title">热门书籍</h2>
      <router-link to="/books" class="more-link">查看全部 →</router-link>
    </div>
    <div class="grid">
      <BookCard v-for="b in hotBooks" :key="b.id" v-bind="b" />
    </div>
  </div>
</template>

<style scoped>
.hero {
  position: relative;
  min-height: min(72vh, 640px);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  margin-top: -64px;
  padding-top: 64px;
}

.hero-media {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  pointer-events: none;
  filter: brightness(1.06) saturate(1.08);
  opacity: 0;
  z-index: 0;
  transition: opacity 1.2s ease-in-out;
  will-change: opacity;
}

.hero-media--active {
  opacity: 1;
  z-index: 1;
}

.hero-media--image {
  background: linear-gradient(135deg, #4a7c8c, #2d4a52);
  background-size: cover;
  background-position: center;
}

.hero-media--fallback {
  background: linear-gradient(135deg, #4a7c8c, #2d4a52);
}

.hero-shade {
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
  background: linear-gradient(
    180deg,
    rgba(0, 0, 0, 0.08) 0%,
    rgba(0, 0, 0, 0.14) 45%,
    rgba(0, 0, 0, 0.22) 100%
  );
}

.hero-video-nav {
  position: absolute;
  inset: 0;
  z-index: 5;
  pointer-events: none;
}

.hero-nav-zone {
  position: absolute;
  bottom: 0;
  top: 38%;
  width: 112px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding-bottom: 28px;
  pointer-events: auto;
}

.hero-nav-zone--left {
  left: 0;
}

.hero-nav-zone--right {
  right: 0;
}

.hero-nav-btn {
  width: 48px;
  height: 48px;
  border: 2px solid rgba(255, 255, 255, 0.85);
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.42);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
  opacity: 0;
  visibility: hidden;
  transform: translateY(10px) scale(0.9);
  transition:
    opacity 0.45s cubic-bezier(0.22, 1, 0.36, 1),
    transform 0.45s cubic-bezier(0.22, 1, 0.36, 1),
    visibility 0.45s,
    background 0.25s ease,
    border-color 0.25s ease,
    box-shadow 0.25s ease;
}

.hero-nav-btn.is-visible {
  opacity: 1;
  visibility: visible;
  transform: translateY(0) scale(1);
}

.hero-nav-btn.is-visible:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.58);
  border-color: #fff;
  transform: translateY(0) scale(1.08);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.42);
}

.hero-nav-btn.is-disabled.is-visible {
  opacity: 0.55;
  cursor: not-allowed;
  border-color: rgba(255, 255, 255, 0.45);
}

.hero-nav-indicator {
  position: absolute;
  left: 50%;
  bottom: 44px;
  transform: translateX(-50%) translateY(10px);
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  color: #fff;
  background: rgba(0, 0, 0, 0.38);
  pointer-events: none;
  backdrop-filter: blur(6px);
  opacity: 0;
  visibility: hidden;
  transition:
    opacity 0.45s cubic-bezier(0.22, 1, 0.36, 1),
    transform 0.45s cubic-bezier(0.22, 1, 0.36, 1),
    visibility 0.45s;
}

.hero-nav-indicator.is-visible {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) translateY(0);
}

.hero-inner {
  position: relative;
  z-index: 2;
  text-align: center;
  padding: 48px 20px 56px;
  width: 100%;
  max-width: 840px;
  margin: 0 auto;
}

.hero-title {
  font-size: clamp(28px, 4vw, 42px);
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.02em;
  margin-bottom: 12px;
  text-shadow: 0 2px 16px rgba(0, 0, 0, 0.35);
}

.hero-subtitle {
  color: rgba(255, 255, 255, 0.88);
  font-size: clamp(15px, 2vw, 18px);
  margin-bottom: 32px;
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.3);
}

.trust-bar {
  background: rgba(26, 32, 44, 0.92);
  color: rgba(255, 255, 255, 0.9);
}

.trust-inner {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding: 20px 20px;
}

.trust-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: center;
  padding: 8px 12px;
}

.trust-item strong {
  font-size: 15px;
  font-weight: 600;
}

.trust-item span {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.65);
}

.section {
  margin-top: 48px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.section-title {
  font-size: 20px;
  margin-bottom: 0;
}

.section-head .section-title {
  margin-bottom: 0;
}

.section > .section-title {
  margin-bottom: 20px;
}

.more-link {
  font-size: 14px;
  color: var(--color-primary);
}

.featured {
  display: flex;
  gap: 24px;
  background: var(--color-surface);
  padding: 24px;
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  transition: transform 0.2s, box-shadow 0.2s;
}

.featured:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.featured img {
  width: 140px;
  aspect-ratio: 3 / 4;
  object-fit: cover;
  border-radius: 8px;
  flex-shrink: 0;
}

.featured-body h3 {
  font-size: 20px;
  margin-bottom: 6px;
}

.author {
  color: var(--color-text-secondary);
  font-size: 14px;
}

.highlight {
  margin-top: 12px;
  color: var(--color-accent);
  line-height: 1.6;
}

.featured-cta {
  display: inline-block;
  margin-top: 16px;
  font-size: 14px;
  color: var(--color-primary);
  font-weight: 500;
}

.cats {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.cat-chip {
  padding: 10px 18px;
  background: var(--color-surface);
  border-radius: 999px;
  border: 1px solid var(--color-border);
  font-size: 14px;
  transition: border-color 0.2s, color 0.2s, background 0.2s;
}

.cat-chip:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: rgba(91, 154, 160, 0.06);
}

.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

@media (max-width: 1023px) {
  .trust-inner {
    grid-template-columns: repeat(2, 1fr);
  }

  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 767px) {
  .hero {
    min-height: 560px;
  }

  .hero-nav-zone {
    width: 72px;
    padding-bottom: 18px;
  }

  .hero-nav-btn {
    width: 40px;
    height: 40px;
  }

  .hero-nav-indicator {
    bottom: 32px;
  }

  .trust-inner {
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .grid {
    grid-template-columns: 1fr;
  }

  .featured {
    flex-direction: column;
  }

  .featured img {
    width: 100%;
    max-width: 200px;
  }
}
</style>
