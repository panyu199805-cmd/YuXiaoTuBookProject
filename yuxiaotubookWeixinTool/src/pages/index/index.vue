<script setup lang="ts">
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { getFeatured, getHotBooks } from '@/api/home'
import { getCategories } from '@/api/site'
import { API_BASE, MP_CLIENT_VERSION, MEDIA_ORIGIN } from '@/config/env'
import HeroVideoLayer from '@/components/HeroVideoLayer.vue'
import BookCard from '@/components/BookCard.vue'
import EmptyState from '@/components/EmptyState.vue'
import SecureImage from '@/components/SecureImage.vue'
import { useSiteStore } from '@/stores/site'
import { resolveMediaUrl } from '@/utils/media'
import type { BookCategory, BookListItem } from '@/types/book'

const siteStore = useSiteStore()
const { bgVideos, bgImage, useVideoBg, promoTitle, dailySentence } = storeToRefs(siteStore)

const featured = ref<BookListItem | null>(null)
const hotBooks = ref<BookListItem[]>([])
const categories = ref<BookCategory[]>([])
const loading = ref(false)
const devApiHint = `${MP_CLIENT_VERSION} ${API_BASE}`

/** 本地 HTTP 媒体无法直接播放视频，需 HTTPS 代理；图片由 SecureImage 处理 */
const canPlayHeroVideo = computed(
  () => useVideoBg.value && bgVideos.value.length > 0 && MEDIA_ORIGIN.startsWith('https://'),
)

async function loadHomeData() {
  loading.value = true
  try {
    await siteStore.fetchConfig()
    const results = await Promise.allSettled([
      getFeatured(),
      getHotBooks(1, 12),
      getCategories(),
    ])
    if (results[0].status === 'fulfilled') featured.value = results[0].value
    if (results[1].status === 'fulfilled') hotBooks.value = results[1].value.list || []
    if (results[2].status === 'fulfilled') categories.value = results[2].value
    results.forEach((r, i) => {
      if (r.status === 'rejected') {
        console.warn('[home] load part failed', i, r.reason)
      }
    })
  } finally {
    loading.value = false
  }
}

onShow(() => {
  loadHomeData()
})

onPullDownRefresh(async () => {
  await loadHomeData()
  uni.stopPullDownRefresh()
})

function goBooks(keyword = '', categoryId?: number) {
  let url = '/pages/books/list'
  const params: string[] = []
  if (keyword) params.push(`keyword=${encodeURIComponent(keyword)}`)
  if (categoryId) params.push(`category_id=${categoryId}`)
  if (params.length) url += `?${params.join('&')}`
  uni.switchTab({ url: '/pages/books/list' })
}

function goDetail(id: number) {
  if (!id || !Number.isFinite(id)) {
    uni.showToast({ title: '书籍 ID 无效', icon: 'none' })
    return
  }
  uni.navigateTo({ url: `/pages/books/detail?id=${id}` })
}
</script>

<template>
  <view class="home">
    <view class="dev-api-hint">{{ devApiHint }}</view>
    <view class="hero" :class="{ 'hero--plain': !canPlayHeroVideo && !bgImage }">
      <HeroVideoLayer v-if="canPlayHeroVideo" :sources="bgVideos" />
      <SecureImage v-else-if="bgImage" class="hero-bg" :src="bgImage" mode="aspectFill" />
      <view class="hero-mask" />
      <view class="hero-content">
        <text class="promo">{{ promoTitle }}</text>
        <text class="daily">{{ dailySentence || '一起沉浸式精读好书' }}</text>
        <view class="search-bar" @tap="goBooks()">
          <text class="placeholder">搜索书名、作者…</text>
        </view>
      </view>
    </view>

    <view class="section container">
      <scroll-view scroll-x class="chips" enable-flex>
        <view
          v-for="c in categories"
          :key="c.id"
          class="chip"
          @tap="goBooks('', c.id)"
        >
          {{ c.name }}
        </view>
      </scroll-view>

      <view v-if="featured" class="featured card" @tap="goDetail(featured.id)">
        <text class="section-title">今日主推</text>
        <view class="featured-row">
          <SecureImage class="featured-cover" :src="resolveMediaUrl(featured.cover, featured.id)" mode="aspectFill" />
          <view class="featured-info">
            <text class="featured-title">{{ featured.title }}</text>
            <text class="featured-meta">{{ featured.author }}</text>
            <text class="featured-highlight">{{ featured.highlight }}</text>
          </view>
        </view>
      </view>

      <view class="section-head">
        <text class="section-title">热门书籍</text>
      </view>
      <view v-if="hotBooks.length" class="grid">
        <view
          v-for="b in hotBooks"
          :key="b.id"
          class="grid-item"
          @tap="goDetail(b.id)"
        >
          <BookCard :book="b" />
        </view>
      </view>
      <EmptyState v-else-if="!loading" text="暂无热门书籍" />
    </view>
  </view>
</template>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.home {
  min-height: 100vh;
}

.dev-api-hint {
  padding: 8rpx 16rpx;
  background: #fff3cd;
  color: #856404;
  font-size: 20rpx;
  word-break: break-all;
  line-height: 1.4;
}

.hero {
  position: relative;
  height: 520rpx;
  background: linear-gradient(135deg, #5b9aa0 0%, #4a8589 100%);
}

.hero--plain .hero-mask {
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.08), rgba(247, 248, 250, 0.85));
}

.hero--plain .promo,
.hero--plain .daily {
  color: #fff;
  text-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.25);
}

.hero-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.hero-mask {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.35), rgba(247, 248, 250, 0.9));
}

.hero-content {
  position: relative;
  z-index: 2;
  padding: 120rpx 32rpx 40rpx;
}

.promo {
  display: block;
  color: #fff;
  font-size: 44rpx;
  font-weight: 700;
}

.daily {
  display: block;
  margin-top: 16rpx;
  color: rgba(255, 255, 255, 0.9);
  font-size: 26rpx;
}

.search-bar {
  margin-top: 32rpx;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 999rpx;
  padding: 20rpx 28rpx;
}

.placeholder {
  color: $color-text-secondary;
}

.section {
  margin-top: -40rpx;
  position: relative;
  z-index: 3;
}

.chips {
  white-space: nowrap;
  margin-bottom: 24rpx;
}

.chip {
  display: inline-block;
  margin-right: 16rpx;
  padding: 12rpx 24rpx;
  background: $color-surface;
  border-radius: 999rpx;
  font-size: 24rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
}

.section-head {
  margin: 24rpx 0 16rpx;
}

.featured-row {
  display: flex;
  margin-top: 16rpx;
  gap: 20rpx;
}

.featured-cover {
  width: 160rpx;
  height: 220rpx;
  border-radius: 12rpx;
  flex-shrink: 0;
}

.featured-info {
  flex: 1;
}

.featured-title {
  display: block;
  font-size: 30rpx;
  font-weight: 600;
}

.featured-meta,
.featured-highlight {
  display: block;
  margin-top: 8rpx;
  color: $color-text-secondary;
  font-size: 24rpx;
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
}
</style>
