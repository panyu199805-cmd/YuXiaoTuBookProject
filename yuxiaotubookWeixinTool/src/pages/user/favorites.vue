<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'
import { listFavorites } from '@/api/favorites'
import BookCard from '@/components/BookCard.vue'
import EmptyState from '@/components/EmptyState.vue'
import { useUserStore } from '@/stores/user'
import type { BookListItem } from '@/types/book'

const userStore = useUserStore()
const books = ref<BookListItem[]>([])
const needLogin = ref(false)

onShow(async () => {
  if (!userStore.isLoggedIn) {
    books.value = []
    needLogin.value = true
    return
  }
  needLogin.value = false
  try {
    books.value = await listFavorites()
  } catch {
    books.value = []
  }
})

function goLogin() {
  uni.navigateTo({ url: '/pages/auth/login?redirect=' + encodeURIComponent('/pages/user/favorites') })
}

function goDetail(id: number) {
  if (!id || !Number.isFinite(id)) return
  uni.navigateTo({ url: `/pages/books/detail?id=${id}` })
}
</script>

<template>
  <view class="page container">
    <view v-if="books.length" class="grid">
      <view v-for="b in books" :key="b.id" class="grid-item" @tap="goDetail(b.id)">
        <BookCard :book="b" />
      </view>
    </view>
    <EmptyState
      v-else-if="needLogin"
      text="登录后查看收藏"
      action-text="去登录"
      @action="goLogin"
    />
    <EmptyState v-else text="暂无收藏" />
  </view>
</template>

<style lang="scss" scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
}
</style>
