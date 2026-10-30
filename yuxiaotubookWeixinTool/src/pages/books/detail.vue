<script setup lang="ts">
import { onLoad, onShow } from '@dcloudio/uni-app'
import { ref, computed } from 'vue'
import {
  addFavorite,
  getBook,
  getPlayAuth,
  getSimilar,
} from '@/api/books'
import { createOrder, mockPayOrder } from '@/api/trade'
import SecureImage from '@/components/SecureImage.vue'
import BookCard from '@/components/BookCard.vue'
import EmptyState from '@/components/EmptyState.vue'
import EbookReader from '@/components/EbookReader.vue'
import { useUserStore } from '@/stores/user'
import { resolveMediaUrl } from '@/utils/media'
import { DEFAULT_EBOOK_CONTENT, DEFAULT_EBOOK_TITLE } from '@/constants/defaultEbookContent'
import type { BookDetail, BookListItem, PlayAuthVideo } from '@/types/book'

const userStore = useUserStore()
const bookId = ref(0)
const book = ref<BookDetail | null>(null)
const similar = ref<BookListItem[]>([])
const loading = ref(false)
const loadError = ref('')
const videoPlaylist = ref<PlayAuthVideo[]>([])
const currentVideoIndex = ref(0)
const videoUrl = ref('')
const videoPoster = ref('')
const fullAccess = ref(true)
const maxDuration = ref<number | null>(null)
const showOrder = ref(false)
const submitting = ref(false)
const orderForm = ref({
  quantity: 1,
  receiver_name: '',
  receiver_phone: '',
  receiver_address: '',
})

function getPageOptions(): Record<string, string | undefined> {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1] as { options?: Record<string, string> } | undefined
  return page?.options || {}
}

function parseBookId(query?: Record<string, string | undefined>): number {
  const q = query && Object.keys(query).length ? query : getPageOptions()
  const raw = q?.id ?? q?.bookId ?? q?.book_id
  if (raw == null || raw === '') return 0
  const id = Number(raw)
  return Number.isFinite(id) && id > 0 ? id : 0
}

function resolveBookId(query?: Record<string, string | undefined>): number {
  const id = parseBookId(query)
  if (id) return id
  return parseBookId(getPageOptions())
}

function applyCurrentVideo() {
  const current = videoPlaylist.value[currentVideoIndex.value]
  if (!current) {
    videoUrl.value = ''
    videoPoster.value = ''
    return
  }
  videoUrl.value = resolveMediaUrl(current.video_url)
  videoPoster.value = resolveMediaUrl(current.poster)
}

function onVideoEnded() {
  if (currentVideoIndex.value < videoPlaylist.value.length - 1) {
    currentVideoIndex.value += 1
    applyCurrentVideo()
  }
}

async function loadDetail() {
  if (!bookId.value) {
    bookId.value = resolveBookId()
  }
  if (!bookId.value) {
    loadError.value = '无效的书籍 ID'
    return
  }

  loading.value = true
  loadError.value = ''
  book.value = null
  similar.value = []
  videoPlaylist.value = []
  currentVideoIndex.value = 0
  videoUrl.value = ''
  videoPoster.value = ''
  fullAccess.value = true
  maxDuration.value = null

  try {
    book.value = await getBook(bookId.value)
  } catch (e) {
    console.error('[detail] getBook failed', bookId.value, e)
    loadError.value = '书籍加载失败，请检查网络后重试'
    return
  } finally {
    loading.value = false
  }

  if (book.value?.has_video) {
    try {
      const playAuth = await getPlayAuth(bookId.value)
      const playlist = playAuth.videos?.length
        ? playAuth.videos
        : [
            {
              video_url: playAuth.video_url,
              poster: playAuth.poster,
              duration: playAuth.duration,
            },
          ]
      videoPlaylist.value = playlist
      fullAccess.value = playAuth.full_access
      maxDuration.value = playAuth.max_duration ?? null
      applyCurrentVideo()
    } catch (e) {
      console.warn('[detail] play-auth failed', bookId.value, e)
    }
  }

  try {
    similar.value = await getSimilar(bookId.value)
  } catch (e) {
    console.warn('[detail] similar failed', bookId.value, e)
  }
}

onLoad((query) => {
  bookId.value = resolveBookId(query as Record<string, string | undefined>)
  loadDetail()
})

onShow(() => {
  if (!bookId.value && !loading.value) {
    const id = resolveBookId()
    if (id) {
      bookId.value = id
      loadDetail()
    }
  }
})

async function onFavorite() {
  if (!userStore.isLoggedIn) {
    uni.navigateTo({ url: `/pages/auth/login?redirect=${encodeURIComponent('/pages/books/detail?id=' + bookId.value)}` })
    return
  }
  await addFavorite(bookId.value)
  uni.showToast({ title: '收藏成功', icon: 'success' })
}

function openOrder() {
  if (!userStore.isLoggedIn) {
    uni.navigateTo({ url: `/pages/auth/login?redirect=${encodeURIComponent('/pages/books/detail?id=' + bookId.value)}` })
    return
  }
  showOrder.value = true
}

async function submitOrder() {
  const f = orderForm.value
  if (!f.receiver_name.trim() || !/^1\d{10}$/.test(f.receiver_phone.trim()) || !f.receiver_address.trim()) {
    uni.showToast({ title: '请填写完整收货信息', icon: 'none' })
    return
  }
  submitting.value = true
  try {
    const order = await createOrder({
      book_id: bookId.value,
      quantity: f.quantity,
      receiver_name: f.receiver_name.trim(),
      receiver_phone: f.receiver_phone.trim(),
      receiver_address: f.receiver_address.trim(),
    })
    await mockPayOrder(order.id)
    uni.showToast({ title: '下单成功', icon: 'success' })
    showOrder.value = false
  } finally {
    submitting.value = false
  }
}

function goDetail(id: number) {
  if (!id || !Number.isFinite(id)) return
  uni.redirectTo({ url: `/pages/books/detail?id=${id}` })
}

const ebookText = computed(() => DEFAULT_EBOOK_CONTENT)

const ebookTitle = computed(() => DEFAULT_EBOOK_TITLE)
</script>

<template>
  <view v-if="loading" class="loading-wrap">
    <text class="loading-text">加载中…</text>
  </view>

  <view v-else-if="book" class="page">
    <view v-if="videoUrl" class="video-section">
      <video
        :key="`${book.id}-${currentVideoIndex}`"
        class="player"
        :src="videoUrl"
        :poster="videoPoster"
        controls
        @ended="onVideoEnded"
      />
      <text v-if="videoPlaylist.length > 1" class="playlist-hint">
        正在播放第 {{ currentVideoIndex + 1 }} / {{ videoPlaylist.length }} 条解读视频
      </text>
      <text v-if="!fullAccess && maxDuration" class="preview-hint">
        游客试看 {{ Math.floor(maxDuration / 60) }} 分钟，登录看全片
      </text>
    </view>

    <view v-else-if="book.has_video === false" class="no-video">
      <SecureImage class="no-video-cover" :src="resolveMediaUrl(book.cover, book.id)" mode="aspectFill" />
      <text class="no-video-tip">解读视频筹备中</text>
    </view>

    <view class="detail container">
      <text class="title">{{ book.title }}</text>
      <text class="meta">{{ book.author }} · {{ book.category?.name || '未分类' }}</text>
      <text v-if="book.highlight" class="highlight">「{{ book.highlight }}」</text>

      <EbookReader
        :title="ebookTitle"
        :teaser="book.summary"
        :ebook-content="ebookText"
      />

      <text v-if="book.target_audience" class="audience">适合：{{ book.target_audience }}</text>
      <text class="price">¥{{ book.price?.toFixed(2) }} · 库存 {{ book.stock ?? 0 }}</text>

      <view class="actions">
        <button class="btn-outline" @tap="onFavorite">收藏</button>
        <button
          class="btn-primary"
          :disabled="(book.stock ?? 0) <= 0"
          @tap="openOrder"
        >
          {{ (book.stock ?? 0) > 0 ? '购买纸质书' : '已售罄' }}
        </button>
      </view>
    </view>

    <view v-if="similar.length" class="similar container">
      <text class="block-title">相似推荐</text>
      <view class="grid">
        <view v-for="b in similar" :key="b.id" class="grid-item" @tap="goDetail(b.id)">
          <BookCard :book="b" />
        </view>
      </view>
    </view>

    <view v-if="showOrder" class="modal">
      <view class="modal-body card">
        <text class="block-title">填写收货信息</text>
        <input v-model="orderForm.receiver_name" class="input" placeholder="收货人" />
        <input v-model="orderForm.receiver_phone" class="input" placeholder="手机号" />
        <input v-model="orderForm.receiver_address" class="input" placeholder="收货地址" />
        <view class="modal-actions">
          <button @tap="showOrder = false">取消</button>
          <button class="btn-primary" :loading="submitting" @tap="submitOrder">提交订单</button>
        </view>
      </view>
    </view>
  </view>

  <EmptyState
    v-else
    :text="loadError || '书籍不存在'"
    :action-text="loadError ? '重试' : undefined"
    @action="loadDetail"
  />
</template>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.loading-wrap {
  padding: 120rpx 40rpx;
  text-align: center;
}

.loading-text {
  color: $color-text-secondary;
  font-size: 28rpx;
}

.page {
  min-height: 100vh;
  background: $color-bg;
  padding-bottom: 40rpx;
}

.video-section {
  margin-bottom: 24rpx;
}

.player {
  width: 100%;
  height: 420rpx;
  background: #000;
}

.playlist-hint,
.preview-hint {
  display: block;
  margin-top: 12rpx;
  padding: 0 32rpx;
  font-size: 24rpx;
  color: $color-text-secondary;
  text-align: center;
}

.no-video {
  padding: 48rpx 32rpx;
  text-align: center;
}

.no-video-cover {
  width: 240rpx;
  height: 320rpx;
  border-radius: 12rpx;
  display: block;
  margin: 0 auto 16rpx;
}

.no-video-tip {
  color: $color-text-secondary;
  font-size: 26rpx;
}

.detail {
  padding-top: 8rpx;
}

.title {
  display: block;
  font-size: 40rpx;
  font-weight: 700;
  line-height: 1.35;
}

.meta {
  display: block;
  margin-top: 12rpx;
  color: $color-text-secondary;
  font-size: 26rpx;
}

.highlight {
  display: block;
  margin-top: 20rpx;
  color: $color-primary-dark;
  font-size: 30rpx;
  line-height: 1.5;
}

.audience {
  display: block;
  margin-top: 20rpx;
  font-size: 26rpx;
  color: $color-text-secondary;
}

.block-title {
  display: block;
  font-size: 30rpx;
  font-weight: 600;
  margin-bottom: 16rpx;
}

.price {
  display: block;
  margin-top: 16rpx;
  color: $color-primary;
  font-size: 32rpx;
  font-weight: 600;
}

.actions {
  display: flex;
  gap: 16rpx;
  margin-top: 28rpx;
}

.btn-outline,
.btn-primary {
  flex: 1;
  font-size: 28rpx;
}

.btn-outline {
  background: #fff;
  border: 1rpx solid $color-primary;
  color: $color-primary;
}

.similar {
  margin-top: 40rpx;
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
  margin-top: 16rpx;
}

.modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32rpx;
  z-index: 100;
}

.modal-body {
  width: 100%;
}

.input {
  background: $color-bg;
  border-radius: 12rpx;
  padding: 20rpx;
  margin-bottom: 16rpx;
}

.modal-actions {
  display: flex;
  gap: 16rpx;
  margin-top: 8rpx;
}
</style>
