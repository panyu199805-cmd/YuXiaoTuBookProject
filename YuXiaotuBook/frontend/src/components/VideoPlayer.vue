<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { protectVideoUrl } from '@/utils/video'

const props = defineProps<{
  src: string
  poster?: string
  maxDuration?: number | null
}>()

const emit = defineEmits<{
  previewEnded: []
}>()

const PLAYBACK_RATES = [0.75, 1, 1.25, 1.5, 2] as const

const playerRef = ref<HTMLElement | null>(null)
const videoRef = ref<HTMLVideoElement | null>(null)
const previewEnded = ref(false)
const playing = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(0.85)
const muted = ref(false)
const rateIndex = ref(1)
const isFullscreen = ref(false)
const showControls = ref(true)
const buffering = ref(false)
const loading = ref(false)

let hideTimer: ReturnType<typeof setTimeout> | null = null
let timeUpdateRaf = 0
let visibilityObserver: IntersectionObserver | null = null

const playbackSrc = computed(() => protectVideoUrl(props.src))

const playbackRate = computed(() => PLAYBACK_RATES[rateIndex.value])
const volumeIcon = computed(() => {
  if (muted.value || volume.value === 0) return 'mute'
  if (volume.value < 0.35) return 'low'
  return 'high'
})

watch(
  () => playbackSrc.value,
  () => {
    previewEnded.value = false
    currentTime.value = 0
    duration.value = 0
    if (videoRef.value) videoRef.value.load()
  },
)

watch(volume, (value) => {
  if (!videoRef.value) return
  videoRef.value.volume = value
  if (value > 0) muted.value = false
})

watch(muted, (value) => {
  if (videoRef.value) videoRef.value.muted = value
})

watch(playbackRate, (value) => {
  if (videoRef.value) videoRef.value.playbackRate = value
})

onMounted(() => {
  document.addEventListener('fullscreenchange', syncFullscreen)
  if (videoRef.value) {
    videoRef.value.volume = volume.value
    videoRef.value.playbackRate = playbackRate.value
  }
  if (playerRef.value) {
    visibilityObserver = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          ensurePreloading()
        }
      },
      { rootMargin: '160px' },
    )
    visibilityObserver.observe(playerRef.value)
  }
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', syncFullscreen)
  visibilityObserver?.disconnect()
  visibilityObserver = null
  if (hideTimer) clearTimeout(hideTimer)
  if (timeUpdateRaf) cancelAnimationFrame(timeUpdateRaf)
  exitFullscreen()
})

function ensurePreloading() {
  const video = videoRef.value
  if (!video || !playbackSrc.value) return
  if (video.preload !== 'auto') video.preload = 'auto'
  if (video.readyState === HTMLMediaElement.HAVE_NOTHING) {
    video.load()
  }
}

function waitUntilCanPlay(video: HTMLVideoElement, timeoutMs = 15000): Promise<void> {
  if (video.readyState >= HTMLMediaElement.HAVE_FUTURE_DATA) {
    return Promise.resolve()
  }
  return new Promise((resolve) => {
    const timer = window.setTimeout(() => resolve(), timeoutMs)
    const done = () => {
      window.clearTimeout(timer)
      resolve()
    }
    video.addEventListener('canplay', done, { once: true })
    video.addEventListener('error', done, { once: true })
  })
}

function syncFullscreen() {
  isFullscreen.value = document.fullscreenElement === playerRef.value
}

function revealControls(autoHide = true) {
  showControls.value = true
  if (hideTimer) clearTimeout(hideTimer)
  if (autoHide && playing.value) {
    hideTimer = setTimeout(() => {
      showControls.value = false
    }, 2800)
  }
}

async function togglePlay() {
  const video = videoRef.value
  if (!video || previewEnded.value) return
  if (!video.paused) {
    video.pause()
    return
  }
  loading.value = true
  ensurePreloading()
  await waitUntilCanPlay(video)
  try {
    await video.play()
  } catch {
    /* ignore autoplay restrictions */
  } finally {
    loading.value = false
  }
}

function onPlay() {
  playing.value = true
  revealControls()
}

function onPause() {
  playing.value = false
  showControls.value = true
  if (hideTimer) clearTimeout(hideTimer)
}

function onLoadedMetadata() {
  duration.value = videoRef.value?.duration || 0
  if (videoRef.value) {
    videoRef.value.volume = volume.value
    videoRef.value.playbackRate = playbackRate.value
  }
}

function onTimeUpdate() {
  if (!videoRef.value) return
  if (timeUpdateRaf) return
  timeUpdateRaf = requestAnimationFrame(() => {
    timeUpdateRaf = 0
    if (!videoRef.value) return
    currentTime.value = videoRef.value.currentTime
    if (!props.maxDuration || previewEnded.value) return
    if (videoRef.value.currentTime >= props.maxDuration) {
      videoRef.value.pause()
      previewEnded.value = true
      emit('previewEnded')
    }
  })
}

function onWaiting() {
  buffering.value = true
}

function onCanPlay() {
  buffering.value = false
}

function onSeek(event: Event) {
  const video = videoRef.value
  if (!video) return
  video.currentTime = Number((event.target as HTMLInputElement).value)
}

function toggleMute() {
  muted.value = !muted.value
  if (!muted.value && volume.value === 0) volume.value = 0.6
}

function onVolumeInput(event: Event) {
  const value = Number((event.target as HTMLInputElement).value)
  volume.value = value
  muted.value = value === 0
}

function cyclePlaybackRate() {
  rateIndex.value = (rateIndex.value + 1) % PLAYBACK_RATES.length
}

async function toggleFullscreen() {
  const el = playerRef.value
  if (!el) return
  try {
    if (document.fullscreenElement === el) await document.exitFullscreen()
    else await el.requestFullscreen()
  } catch {
    /* ignore */
  }
}

function exitFullscreen() {
  if (document.fullscreenElement === playerRef.value) {
    void document.exitFullscreen()
  }
}

function formatTime(seconds: number) {
  if (!seconds || !Number.isFinite(seconds)) return '00:00'
  const minutes = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
}
</script>

<template>
  <div
    ref="playerRef"
    class="book-video-player"
    :class="{ 'is-playing': playing, 'is-fullscreen': isFullscreen }"
    @mousemove="revealControls()"
    @mouseleave="showControls = !playing"
  >
    <video
      ref="videoRef"
      :src="playbackSrc"
      :poster="poster"
      class="book-video"
      playsinline
      webkit-playsinline
      preload="auto"
      disablepictureinpicture
      disableremoteplayback
      controlslist="nodownload noremoteplayback nofullscreen noplaybackrate"
      x-webkit-airplay="deny"
      referrerpolicy="no-referrer"
      @click="togglePlay"
      @contextmenu.prevent
      @play="onPlay"
      @pause="onPause"
      @loadedmetadata="onLoadedMetadata"
      @timeupdate="onTimeUpdate"
      @waiting="onWaiting"
      @canplay="onCanPlay"
    />

    <div class="video-download-shield" aria-hidden="true" @contextmenu.prevent />

    <div v-if="loading || (buffering && playing)" class="book-video-loading" aria-hidden="true">
      <span class="book-video-loading-dot" />
    </div>

    <button
      v-if="!playing && !previewEnded && !loading"
      type="button"
      class="book-video-center-play"
      aria-label="播放"
      @click.stop="togglePlay"
    >
      <svg viewBox="0 0 24 24" width="34" height="34" fill="currentColor">
        <path d="M8 5.14v13.72L19 12 8 5.14z" />
      </svg>
    </button>

    <div class="book-video-bar" :class="{ 'is-hidden': !showControls && playing }">
      <input
        class="book-video-progress"
        type="range"
        min="0"
        :max="duration || 0"
        step="0.1"
        :value="currentTime"
        @input="onSeek"
        @click.stop
      />

      <div class="book-video-bar-row">
        <div class="book-video-left">
          <button type="button" class="vp-btn" aria-label="播放/暂停" @click.stop="togglePlay">
            <svg v-if="playing" viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
              <path d="M6 5h4v14H6V5zm8 0h4v14h-4V5z" />
            </svg>
            <svg v-else viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
              <path d="M8 5.14v13.72L19 12 8 5.14z" />
            </svg>
          </button>
          <span class="book-video-time">
            {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
          </span>
        </div>

        <div class="book-video-right">
          <button
            type="button"
            class="vp-btn vp-btn--text"
            :title="`播放速度 ${playbackRate}x`"
            @click.stop="cyclePlaybackRate"
          >
            {{ playbackRate }}x
          </button>

          <div class="vp-volume" @click.stop>
            <button type="button" class="vp-btn" aria-label="静音" @click="toggleMute">
              <svg v-if="volumeIcon === 'mute'" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 5L6 9H3v6h3l5 4V5z" stroke-linecap="round" stroke-linejoin="round" />
                <path d="M16 9l5 6M21 9l-5 6" stroke-linecap="round" />
              </svg>
              <svg v-else-if="volumeIcon === 'low'" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 5L6 9H3v6h3l5 4V5z" stroke-linecap="round" stroke-linejoin="round" />
                <path d="M15.54 8.46a5 5 0 010 7.08" stroke-linecap="round" />
              </svg>
              <svg v-else viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 5L6 9H3v6h3l5 4V5z" stroke-linecap="round" stroke-linejoin="round" />
                <path d="M15.54 8.46a5 5 0 010 7.08M19.07 4.93a10 10 0 010 14.14" stroke-linecap="round" />
              </svg>
            </button>
            <input
              class="vp-volume-range"
              type="range"
              min="0"
              max="1"
              step="0.05"
              :value="muted ? 0 : volume"
              @input="onVolumeInput"
            />
          </div>

          <button
            type="button"
            class="vp-btn"
            :aria-label="isFullscreen ? '退出全屏' : '全屏'"
            :title="isFullscreen ? '退出全屏' : '全屏'"
            @click.stop="toggleFullscreen"
          >
            <svg v-if="!isFullscreen" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M8 3H3v5M16 3h5v5M16 21h5v-5M8 21H3v-5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            <svg v-else viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 14h6v6M14 20v-6h6M20 10h-6V4M10 4v6H4" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <div v-if="previewEnded" class="book-video-preview-tip">
      试看已结束，登录后可观看完整视频
    </div>
  </div>
</template>

<style scoped>
.book-video-player {
  position: relative;
  background: #0f1418;
  border-radius: var(--radius-card, 12px);
  overflow: hidden;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.18);
}

.book-video-player.is-fullscreen {
  border-radius: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.book-video {
  width: 100%;
  max-height: 480px;
  display: block;
  cursor: pointer;
  background: #000;
  transform: translateZ(0);
  backface-visibility: hidden;
}

.book-video-loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  background: rgba(0, 0, 0, 0.22);
}

.book-video-loading-dot {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: 3px solid rgba(255, 255, 255, 0.35);
  border-top-color: #fff;
  animation: book-video-spin 0.75s linear infinite;
}

@keyframes book-video-spin {
  to {
    transform: rotate(360deg);
  }
}

.book-video-player.is-fullscreen .book-video {
  max-height: none;
  height: 100%;
  object-fit: contain;
}

.book-video-center-play {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 72px;
  height: 72px;
  border: none;
  border-radius: 50%;
  background: rgba(91, 154, 160, 0.92);
  color: #fff;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.28);
  transition: transform 0.18s ease, background 0.18s ease;
}

.book-video-center-play:hover {
  transform: translate(-50%, -50%) scale(1.05);
  background: rgba(74, 133, 139, 0.98);
}

.book-video-bar {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 0 12px 10px;
  background: linear-gradient(180deg, transparent 0%, rgba(0, 0, 0, 0.55) 38%, rgba(0, 0, 0, 0.88) 100%);
  transition: opacity 0.22s ease;
}

.book-video-bar.is-hidden {
  opacity: 0;
  pointer-events: none;
}

.book-video-progress {
  width: 100%;
  height: 4px;
  margin: 0 0 8px;
  accent-color: var(--color-primary, #5b9aa0);
  cursor: pointer;
}

.book-video-bar-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.book-video-left,
.book-video-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.book-video-right {
  margin-left: auto;
}

.book-video-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.92);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.vp-btn {
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s ease, color 0.15s ease;
}

.vp-btn:hover {
  background: rgba(91, 154, 160, 0.45);
}

.vp-btn--text {
  width: auto;
  min-width: 44px;
  padding: 0 10px;
  font-size: 12px;
  font-weight: 600;
  font-family: inherit;
}

.vp-volume {
  display: flex;
  align-items: center;
  gap: 4px;
}

.vp-volume-range {
  width: 0;
  opacity: 0;
  accent-color: var(--color-primary, #5b9aa0);
  transition: width 0.2s ease, opacity 0.2s ease;
  cursor: pointer;
}

.vp-volume:hover .vp-volume-range,
.vp-volume:focus-within .vp-volume-range {
  width: 72px;
  opacity: 1;
}

.book-video-preview-tip {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 64px;
  background: rgba(0, 0, 0, 0.78);
  color: #fff;
  text-align: center;
  padding: 12px;
  font-size: 14px;
  pointer-events: none;
}

@media (max-width: 640px) {
  .book-video-center-play {
    width: 60px;
    height: 60px;
  }

  .vp-volume:hover .vp-volume-range,
  .vp-volume:focus-within .vp-volume-range {
    width: 56px;
  }

  .book-video-time {
    font-size: 11px;
  }
}
</style>
