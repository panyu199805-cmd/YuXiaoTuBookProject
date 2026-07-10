<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  sources: string[]
}>()

const current = ref(0)
const videoSrc = ref('')

watch(
  () => props.sources,
  (list) => {
    if (list?.length) {
      current.value = 0
      videoSrc.value = list[0]
    }
  },
  { immediate: true },
)

function onEnded() {
  if (!props.sources.length) return
  current.value = (current.value + 1) % props.sources.length
  videoSrc.value = props.sources[current.value]
}
</script>

<template>
  <view v-if="videoSrc" class="hero-video">
    <video
      class="video"
      :src="videoSrc"
      autoplay
      loop
      muted
      :show-center-play-btn="false"
      :controls="false"
      object-fit="cover"
      @ended="onEnded"
    />
    <view class="overlay" />
  </view>
</template>

<style lang="scss" scoped>
.hero-video {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.video {
  width: 100%;
  height: 100%;
}

.overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.35) 0%, rgba(0, 0, 0, 0.15) 100%);
}
</style>
