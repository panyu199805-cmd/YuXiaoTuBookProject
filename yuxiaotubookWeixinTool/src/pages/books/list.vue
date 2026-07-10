<script setup lang="ts">
import { onLoad, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import { ref } from 'vue'
import { listBooks } from '@/api/books'
import { getCategories } from '@/api/site'
import BookCard from '@/components/BookCard.vue'
import EmptyState from '@/components/EmptyState.vue'
import type { BookListItem, BookCategory } from '@/types/book'

const books = ref<BookListItem[]>([])
const categories = ref<BookCategory[]>([])
const keyword = ref('')
const categoryId = ref<number | undefined>()
const sort = ref<'hot' | 'new'>('hot')
const page = ref(1)
const total = ref(0)
const loading = ref(false)

async function loadBooks(reset = false) {
  if (loading.value) return
  if (reset) {
    page.value = 1
    books.value = []
  }
  loading.value = true
  try {
    const res = await listBooks({
      page: page.value,
      page_size: 12,
      sort: sort.value,
      keyword: keyword.value || undefined,
      category_id: categoryId.value,
    })
    total.value = res.total
    books.value = reset ? res.list : [...books.value, ...res.list]
  } finally {
    loading.value = false
  }
}

onLoad((query) => {
  if (query?.keyword) keyword.value = decodeURIComponent(String(query.keyword))
  if (query?.category_id) categoryId.value = Number(query.category_id)
  getCategories().then((cats) => {
    categories.value = cats
  })
  loadBooks(true)
})

onPullDownRefresh(async () => {
  await loadBooks(true)
  uni.stopPullDownRefresh()
})

onReachBottom(() => {
  if (books.value.length < total.value) {
    page.value += 1
    loadBooks(false)
  }
})

function selectCategory(id?: number) {
  categoryId.value = id
  loadBooks(true)
}

function toggleSort() {
  sort.value = sort.value === 'hot' ? 'new' : 'hot'
  loadBooks(true)
}

function goDetail(id: number) {
  uni.navigateTo({ url: `/pages/books/detail?id=${id}` })
}
</script>

<template>
  <view class="page container">
    <view class="toolbar">
      <scroll-view scroll-x class="chips" enable-flex>
        <view class="chip" :class="{ active: !categoryId }" @tap="selectCategory()">全部</view>
        <view
          v-for="c in categories"
          :key="c.id"
          class="chip"
          :class="{ active: categoryId === c.id }"
          @tap="selectCategory(c.id)"
        >
          {{ c.name }}
        </view>
      </scroll-view>
      <view class="sort" @tap="toggleSort">{{ sort === 'hot' ? '热门' : '最新' }}</view>
    </view>

    <view v-if="books.length" class="grid">
      <BookCard v-for="b in books" :key="b.id" :book="b" @tap="goDetail" />
    </view>
    <EmptyState v-else-if="!loading" text="暂无书籍" />
  </view>
</template>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.toolbar {
  margin-bottom: 20rpx;
}

.chips {
  white-space: nowrap;
  margin-bottom: 16rpx;
}

.chip {
  display: inline-block;
  margin-right: 12rpx;
  padding: 10rpx 22rpx;
  background: $color-surface;
  border-radius: 999rpx;
  font-size: 24rpx;
}

.chip.active {
  background: $color-primary;
  color: #fff;
}

.sort {
  font-size: 24rpx;
  color: $color-primary;
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
}
</style>
