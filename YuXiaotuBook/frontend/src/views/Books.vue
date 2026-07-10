<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useHead } from '@unhead/vue'
import BookCard from '@/components/BookCard.vue'
import { request } from '@/api/client'
import { useBookSearchSuggest } from '@/composables/useBookSearchSuggest'
import BookSearchSuggestList from '@/components/BookSearchSuggestList.vue'

useHead({ title: '书单 - 宇小兔每日读书' })

const route = useRoute()
const router = useRouter()
const books = ref<any[]>([])
const categories = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const categoryId = ref<number | undefined>()
const sort = ref('hot')
const keyword = ref('')
const suggestEnabled = computed(() => true)

const { suggestions, showSuggestions, activeIndex, hideSuggestions, moveActive } =
  useBookSearchSuggest(keyword, suggestEnabled)

async function load() {
  const res = await request<any>({
    url: '/books',
    params: {
      page: page.value,
      page_size: 12,
      sort: sort.value,
      keyword: keyword.value || undefined,
      category_id: categoryId.value,
    },
  })
  if (res.code === 200) {
    books.value = res.data.list
    total.value = res.data.total
  }
}

onMounted(async () => {
  const cats = await request<any[]>({ url: '/categories' })
  if (cats.code === 200) categories.value = cats.data || []
  if (route.query.category_id) categoryId.value = Number(route.query.category_id)
  if (route.query.keyword) keyword.value = String(route.query.keyword)
  load()
})

watch(() => route.query.category_id, (v) => {
  categoryId.value = v ? Number(v) : undefined
  page.value = 1
  load()
})

watch(() => route.query.keyword, (v) => {
  keyword.value = v ? String(v) : ''
  page.value = 1
  load()
})

function onSearch() {
  hideSuggestions()
  load()
}

function pickSuggestion(id: number) {
  hideSuggestions()
  router.push(`/books/${id}`)
}

function onSearchKeydown(e: KeyboardEvent) {
  if (!showSuggestions.value || !suggestions.value.length) return
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    moveActive(1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    moveActive(-1)
  } else if (e.key === 'Enter' && activeIndex.value >= 0) {
    e.preventDefault()
    pickSuggestion(suggestions.value[activeIndex.value].id)
  } else if (e.key === 'Escape') {
    hideSuggestions()
  }
}

function onSearchFocus() {
  if (keyword.value.trim() && suggestions.value.length) {
    showSuggestions.value = true
  }
}

function onSearchBlur() {
  setTimeout(hideSuggestions, 150)
}
</script>

<template>
  <div class="container page">
    <h1 class="page-title">书籍视频书单</h1>
    <div class="toolbar">
      <div class="search-field">
        <input
          v-model="keyword"
          placeholder="搜索书名或作者"
          autocomplete="off"
          @keyup.enter="onSearch"
          @keydown="onSearchKeydown"
          @focus="onSearchFocus"
          @blur="onSearchBlur"
        />
        <BookSearchSuggestList
          v-if="showSuggestions && suggestions.length"
          class="suggest-dropdown"
          :items="suggestions"
          :active-index="activeIndex"
          variant="page"
          @pick="pickSuggestion"
        />
      </div>
      <select v-model="categoryId" @change="load">
        <option :value="undefined">全部分类</option>
        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <select v-model="sort" @change="load">
        <option value="hot">最热</option>
        <option value="new">最新</option>
      </select>
      <button class="btn btn-primary" @click="onSearch">搜索</button>
    </div>
    <div class="grid">
      <BookCard v-for="b in books" :key="b.id" v-bind="b" />
    </div>
    <p v-if="!books.length" class="empty">暂无书籍</p>
  </div>
</template>

<style scoped>
.page { padding-top: 32px; }
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}
.search-field {
  position: relative;
  flex: 1;
  min-width: 220px;
}
.toolbar input, .toolbar select {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
}
.search-field input {
  width: 100%;
  box-sizing: border-box;
}
.suggest-dropdown {
  position: absolute;
  left: 0;
  right: 0;
  top: calc(100% + 6px);
  z-index: 30;
}
.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}
.empty { text-align: center; color: var(--color-text-secondary); padding: 48px; }
@media (max-width: 1023px) { .grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 767px) { .grid { grid-template-columns: 1fr; } }
</style>
