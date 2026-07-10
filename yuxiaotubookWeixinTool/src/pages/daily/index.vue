<script setup lang="ts">
import { onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'
import { getTodayDaily, likeDaily, listDaily } from '@/api/daily'
import EmptyState from '@/components/EmptyState.vue'
import { resolveMediaUrl } from '@/utils/media'
import type { DailyItem } from '@/types/daily'

const today = ref<DailyItem | null>(null)
const list = ref<DailyItem[]>([])
const page = ref(1)
const total = ref(0)
const loading = ref(false)

async function loadData(reset = false) {
  if (reset) {
    page.value = 1
    list.value = []
  }
  loading.value = true
  try {
    const [t, archive] = await Promise.all([
      getTodayDaily(),
      listDaily(page.value, 10),
    ])
    today.value = t
    total.value = archive.total
    list.value = reset ? archive.list : [...list.value, ...archive.list]
  } finally {
    loading.value = false
  }
}

onShow(() => loadData(true))

onPullDownRefresh(async () => {
  await loadData(true)
  uni.stopPullDownRefresh()
})

onReachBottom(() => {
  if (list.value.length < total.value) {
    page.value += 1
    loadData(false)
  }
})

async function onLike(id: number) {
  await likeDaily(id)
  await loadData(true)
}

function goDetail(bookId?: number) {
  if (!bookId) return
  uni.navigateTo({ url: `/pages/books/detail?id=${bookId}` })
}
</script>

<template>
  <view class="page container">
    <view v-if="today" class="card today">
      <text class="label">今日读书</text>
      <text class="sentence">{{ today.daily_sentence }}</text>
      <text class="intro">{{ today.daily_intro }}</text>
      <view class="row">
        <text class="likes">👍 {{ today.like_count }}</text>
        <button size="mini" @tap="onLike(today.id)">点赞</button>
        <button size="mini" @tap="goDetail(today.book_id)">查看书籍</button>
      </view>
    </view>

    <text class="section-title">历史归档</text>
    <view v-for="item in list" :key="item.id" class="card" @tap="goDetail(item.book_id)">
      <text class="date">{{ item.publish_date }}</text>
      <text class="sentence">{{ item.daily_sentence }}</text>
      <text class="likes">👍 {{ item.like_count }}</text>
    </view>
    <EmptyState v-if="!today && !list.length && !loading" />
  </view>
</template>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.label {
  color: $color-primary;
  font-size: 24rpx;
}

.sentence {
  display: block;
  margin-top: 12rpx;
  font-size: 32rpx;
  font-weight: 600;
  line-height: 1.5;
}

.intro,
.date {
  display: block;
  margin-top: 12rpx;
  color: $color-text-secondary;
  font-size: 26rpx;
  line-height: 1.6;
}

.row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 20rpx;
}

.likes {
  font-size: 24rpx;
  color: $color-text-secondary;
}

.section-title {
  display: block;
  margin: 24rpx 0 16rpx;
  font-size: 30rpx;
  font-weight: 600;
}
</style>
