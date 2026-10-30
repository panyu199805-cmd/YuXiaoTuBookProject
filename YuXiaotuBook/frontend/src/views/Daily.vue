<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { request } from '@/api/client'
import { inlineCoverFallback, placeholderCover, resolveMediaUrl } from '@/utils/media'

const router = useRouter()
const today = ref<any>(null)
const list = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const todayCover = ref('')

function onTodayCoverError() {
  if (!today.value?.book) return
  const fallback = placeholderCover(today.value.book.id)
  todayCover.value =
    todayCover.value === fallback
      ? inlineCoverFallback(today.value.book.title, today.value.book.id)
      : fallback
}

async function load() {
  const [t, l] = await Promise.all([
    request<any>({ url: '/daily/today' }),
    request<any>({ url: '/daily/list', params: { page: page.value, page_size: 10 } }),
  ])
  if (t.code === 200) {
    today.value = t.data
    todayCover.value = resolveMediaUrl(t.data?.book?.cover, t.data?.book?.id)
  }
  if (l.code === 200) {
    list.value = l.data.list
    total.value = l.data.total
  }
}

async function like(id: number) {
  await request({ url: `/daily/${id}/like`, method: 'POST' })
  load()
}

function goBook(id: number) {
  router.push(`/books/${id}`)
}

onMounted(load)
</script>

<template>
  <div class="container page">
    <h1 class="page-title">每日读书</h1>

    <section v-if="today" class="today-card">
      <div class="badge">今日推荐</div>
      <p class="sentence">「{{ today.daily_sentence }}」</p>
      <p v-if="today.daily_intro" class="intro">{{ today.daily_intro }}</p>
      <div v-if="today.book" class="book-row" @click="goBook(today.book.id)">
        <img :src="todayCover" :alt="today.book.title" class="cover" @error="onTodayCoverError" />
        <div>
          <h3>{{ today.book.title }}</h3>
          <p class="meta">{{ today.book.author }}</p>
        </div>
      </div>
      <button class="btn btn-outline" @click="like(today.id)">点赞 {{ today.like_count }}</button>
    </section>

    <section class="archive">
      <h2>历史归档</h2>
      <div class="timeline">
        <div v-for="item in list" :key="item.id" class="timeline-item">
          <div class="date">{{ item.publish_date }}</div>
          <div class="card" @click="goBook(item.book_id)">
            <p class="sentence-sm">「{{ item.daily_sentence }}」</p>
            <p v-if="item.book" class="meta">{{ item.book.title }} · {{ item.book.author }}</p>
            <span class="likes">👍 {{ item.like_count }}</span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.page { padding: 32px 20px 48px; }
.today-card {
  background: var(--color-surface);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  padding: 28px;
  margin-bottom: 40px;
}
.badge {
  display: inline-block;
  background: var(--color-primary);
  color: #fff;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  margin-bottom: 16px;
}
.sentence { font-size: 22px; color: var(--color-accent); margin-bottom: 12px; }
.intro { color: var(--color-text-secondary); margin-bottom: 20px; }
.book-row {
  display: flex;
  gap: 16px;
  align-items: center;
  cursor: pointer;
  margin-bottom: 16px;
}
.cover { width: 80px; border-radius: 6px; }
.meta { color: var(--color-text-secondary); font-size: 14px; }
.archive h2 { margin-bottom: 20px; }
.timeline { display: flex; flex-direction: column; gap: 16px; }
.timeline-item { display: flex; gap: 16px; }
.date { width: 100px; color: var(--color-text-secondary); font-size: 14px; padding-top: 12px; }
.card {
  flex: 1;
  background: var(--color-surface);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  padding: 16px 20px;
  cursor: pointer;
}
.sentence-sm { color: var(--color-text); margin-bottom: 8px; }
.likes { font-size: 12px; color: var(--color-text-secondary); }

@media (max-width: 767px) {
  .page { padding: 24px 12px 40px; }
  .sentence { font-size: 18px; }
  .book-row { flex-direction: column; align-items: flex-start; }
  .today-card { padding: 20px 16px; }
  .timeline-item { flex-direction: column; gap: 8px; }
  .date { width: auto; }
}
</style>
