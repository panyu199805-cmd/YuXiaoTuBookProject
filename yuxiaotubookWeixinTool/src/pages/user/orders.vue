<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'
import { listOrders } from '@/api/trade'
import EmptyState from '@/components/EmptyState.vue'
import { useUserStore } from '@/stores/user'
import type { OrderInfo } from '@/types/user'

const userStore = useUserStore()
const orders = ref<OrderInfo[]>([])
const needLogin = ref(false)

onShow(async () => {
  if (!userStore.isLoggedIn) {
    orders.value = []
    needLogin.value = true
    return
  }
  needLogin.value = false
  try {
    orders.value = await listOrders()
  } catch {
    orders.value = []
  }
})

function goLogin() {
  uni.navigateTo({ url: '/pages/auth/login?redirect=' + encodeURIComponent('/pages/user/orders') })
}
</script>

<template>
  <view class="page container">
    <view v-for="o in orders" :key="o.id" class="card">
      <view class="head">
        <text>{{ o.order_no }}</text>
        <text class="status">{{ o.status_label || o.status }}</text>
      </view>
      <view v-for="(item, idx) in o.items" :key="idx">
        <text>{{ item.book_title }} x{{ item.quantity }}</text>
      </view>
      <text class="amount">¥{{ o.total_amount?.toFixed(2) }}</text>
    </view>
    <EmptyState
      v-if="needLogin"
      text="登录后查看订单"
      action-text="去登录"
      @action="goLogin"
    />
    <EmptyState v-else-if="!orders.length" text="暂无订单" />
  </view>
</template>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.status {
  color: $color-primary;
}

.amount {
  display: block;
  margin-top: 12rpx;
  font-weight: 600;
}
</style>
