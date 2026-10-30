<script setup lang="ts">
import { onMounted, ref } from 'vue'
import BookCard from '@/components/BookCard.vue'
import { request } from '@/api/client'

const items = ref<any[]>([])

async function load() {
  const res = await request<any[]>({ url: '/history' })
  if (res.code === 200) items.value = res.data
}

onMounted(load)
</script>

<template>
  <div class="container page">
    <h1 class="page-title">浏览记录</h1>
    <div v-if="items.length" class="grid">
      <BookCard v-for="b in items" :key="b.id" v-bind="b" />
    </div>
    <p v-else class="empty">暂无浏览记录，去书单看看吧</p>
  </div>
</template>

<style scoped>
.page { padding: 32px 20px 48px; }
.grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.empty { color: var(--color-text-secondary); text-align: center; padding: 60px 0; }
@media (max-width: 1023px) { .grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 767px) { .grid { grid-template-columns: 1fr; } }
</style>
