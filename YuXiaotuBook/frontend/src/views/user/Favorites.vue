<script setup lang="ts">
import { onMounted, ref } from 'vue'
import BookCard from '@/components/BookCard.vue'
import { request } from '@/api/client'

const books = ref<any[]>([])

onMounted(async () => {
  const res = await request<any[]>({ url: '/favorites' })
  if (res.code === 200) books.value = res.data
})
</script>

<template>
  <div class="container page">
    <h1 class="page-title">我的收藏</h1>
    <div class="grid">
      <BookCard v-for="b in books" :key="b.id" v-bind="b" />
    </div>
    <p v-if="!books.length" class="empty">暂无收藏</p>
  </div>
</template>

<style scoped>
.page { padding-top: 32px; }
.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}
.empty { text-align: center; color: var(--color-text-secondary); }

@media (max-width: 1023px) { .grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 767px) { .grid { grid-template-columns: 1fr; } }
</style>
