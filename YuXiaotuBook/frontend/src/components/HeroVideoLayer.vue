<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { protectVideoUrl } from '@/utils/video'

const props = withDefaults(
  defineProps<{
    src?: string
    active?: boolean
    loop?: boolean
  }>(),
  {
    src: '',
    active: false,
    loop: false,
  },
)

const emit = defineEmits<{
  loadeddata: []
  ended: []
  error: []
}>()

const videoRef = ref<HTMLVideoElement | null>(null)

const playbackSrc = computed(() => protectVideoUrl(props.src))

async function playVideo() {
  const video = videoRef.value
  if (!video || !playbackSrc.value) return
  try {
    if (video.readyState < HTMLMediaElement.HAVE_FUTURE_DATA) {
      video.load()
    }
    await video.play()
  } catch {
    /* ignore autoplay block */
  }
}

function pauseVideo() {
  videoRef.value?.pause()
}

function prepareBuffer() {
  const video = videoRef.value
  if (!video || !playbackSrc.value) return
  if (video.readyState < HTMLMediaElement.HAVE_METADATA) {
    video.load()
  }
}

watch(
  () => playbackSrc.value,
  (url) => {
    if (!url) return
    prepareBuffer()
  },
)

watch(
  () => props.active,
  (active) => {
    if (active) void playVideo()
    else pauseVideo()
  },
)

onMounted(() => {
  prepareBuffer()
  if (props.active) void playVideo()
})

onUnmounted(() => {
  pauseVideo()
})

defineExpose({
  get el() {
    return videoRef.value
  },
  prepareBuffer,
})
</script>

<template>
  <div class="hero-video-layer" :class="{ 'hero-video-layer--active': active }">
    <video
      ref="videoRef"
      class="hero-video"
      :src="playbackSrc || undefined"
      :loop="loop"
      muted
      playsinline
      webkit-playsinline
      disablepictureinpicture
      disableremoteplayback
      controlslist="nodownload noremoteplayback nofullscreen"
      x-webkit-airplay="deny"
      referrerpolicy="no-referrer"
      preload="auto"
      tabindex="-1"
      aria-hidden="true"
      @loadeddata="emit('loadeddata')"
      @ended="emit('ended')"
      @error="emit('error')"
    />
    <div class="video-download-shield" aria-hidden="true" @contextmenu.prevent />
  </div>
</template>

<style scoped>
.hero-video-layer {
  position: absolute;
  inset: 0;
  opacity: 0;
  z-index: 0;
  transition: opacity 1.2s ease-in-out;
  will-change: opacity;
  pointer-events: none;
  overflow: hidden;
  background: #0a1628;
}

.hero-video-layer--active {
  opacity: 1;
  z-index: 1;
}

.hero-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transform: translateZ(0);
  backface-visibility: hidden;
}
</style>
