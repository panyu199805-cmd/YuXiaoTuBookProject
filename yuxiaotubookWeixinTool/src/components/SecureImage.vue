<script setup lang="ts">
import { ref, watch } from 'vue'
import { toMpSafeMediaUrl } from '@/utils/secureMedia'

const props = withDefaults(
  defineProps<{
    src?: string
    mode?: string
    lazyLoad?: boolean
  }>(),
  { mode: 'aspectFill', lazyLoad: true },
)

const emit = defineEmits<{ error: [] }>()

const displaySrc = ref('')

watch(
  () => props.src,
  async (url) => {
    if (!url) {
      displaySrc.value = ''
      return
    }
    displaySrc.value = await toMpSafeMediaUrl(url)
  },
  { immediate: true },
)

function onError() {
  emit('error')
}
</script>

<template>
  <image
    v-if="displaySrc"
    class="secure-image"
    :src="displaySrc"
    :mode="mode"
    :lazy-load="lazyLoad"
    @error="onError"
  />
</template>

<style scoped>
.secure-image {
  width: 100%;
  height: 100%;
}
</style>
