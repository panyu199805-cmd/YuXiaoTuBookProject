<script setup lang="ts">
import { onLoad } from '@dcloudio/uni-app'
import { ref } from 'vue'
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
import { useUserStore } from '@/stores/user'
import { resolveMediaUrl } from '@/utils/media'
import type { BookDetail, BookListItem, PlayAuth } from '@/types/book'

const userStore = useUserStore()
const bookId = ref(0)
const book = ref<BookDetail | null>(null)
const similar = ref<BookListItem[]>([])
const playAuth = ref<PlayAuth | null>(null)
const videoUrl = ref('')
const showOrder = ref(false)
const submitting = ref(false)
const orderForm = ref({
  quantity: 1,
  receiver_name: '',
  receiver_phone: '',
  receiver_address: '',
})

async function loadDetail() {
  if (!bookId.value) return
  book.value = await getBook(bookId.value)
  similar.value = await getSimilar(bookId.value)
  if (book.value?.has_video) {
    playAuth.value = await getPlayAuth(bookId.value)
    videoUrl.value = resolveMediaUrl(playAuth.value.video_url)
  }
}

onLoad((query) => {
  bookId.value = Number(query?.id || 0)
  loadDetail()
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
  uni.redirectTo({ url: `/pages/books/detail?id=${id}` })
}
</script>

<template>
  <view v-if="book" class="page container">
    <SecureImage class="cover" :src="resolveMediaUrl(book.cover, book.id)" mode="aspectFill" />
    <text class="title">{{ book.title }}</text>
    <text class="meta">{{ book.author }} · {{ book.category?.name }}</text>
    <text class="price">¥{{ book.price?.toFixed(2) }}</text>
    <text class="summary">{{ book.summary }}</text>

    <view v-if="videoUrl" class="card">
      <text class="block-title">解读视频</text>
      <video
        class="player"
        :src="videoUrl"
        controls
        :poster="resolveMediaUrl(playAuth?.poster)"
      />
      <text v-if="playAuth && !playAuth.full_access" class="tip">
        试看 {{ playAuth.max_duration || 180 }} 秒，登录后可看全片
      </text>
    </view>

    <view v-if="book.ebook_content" class="card">
      <text class="block-title">{{ book.ebook_title || '电子书解读' }}</text>
      <text class="ebook">{{ book.ebook_content }}</text>
    </view>

    <view class="actions">
      <button class="btn-outline" @tap="onFavorite">收藏</button>
      <button class="btn-primary" @tap="openOrder">购买纸质书</button>
    </view>

    <view v-if="similar.length" class="similar">
      <text class="block-title">相似推荐</text>
      <view class="grid">
        <BookCard v-for="b in similar" :key="b.id" :book="b" @tap="goDetail" />
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
  <EmptyState v-else text="书籍不存在" />
</template>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.cover {
  width: 240rpx;
  height: 320rpx;
  border-radius: 12rpx;
  display: block;
  margin: 0 auto 24rpx;
}

.title {
  display: block;
  text-align: center;
  font-size: 36rpx;
  font-weight: 700;
}

.meta,
.price,
.summary {
  display: block;
  text-align: center;
  margin-top: 12rpx;
}

.price {
  color: $color-primary;
  font-weight: 600;
}

.summary {
  color: $color-text-secondary;
  font-size: 26rpx;
  line-height: 1.6;
  margin: 24rpx 0;
}

.block-title {
  display: block;
  font-size: 30rpx;
  font-weight: 600;
  margin-bottom: 16rpx;
}

.player {
  width: 100%;
  height: 400rpx;
  border-radius: 12rpx;
}

.tip {
  display: block;
  margin-top: 12rpx;
  font-size: 22rpx;
  color: $color-text-secondary;
}

.ebook {
  white-space: pre-wrap;
  line-height: 1.7;
  font-size: 26rpx;
}

.actions {
  display: flex;
  gap: 16rpx;
  margin: 24rpx 0;
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

.grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
}

.modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32rpx;
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
