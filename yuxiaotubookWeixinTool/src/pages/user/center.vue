<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'
import { getMemberStatus } from '@/api/trade'
import { getShippingOrders } from '@/api/user'
import { useUserStore } from '@/stores/user'
import type { MemberStatus, OrderInfo } from '@/types/user'

const userStore = useUserStore()
const memberStatus = ref<MemberStatus | null>(null)
const shippingOrders = ref<OrderInfo[]>([])

async function load() {
  if (!userStore.isLoggedIn) return
  await userStore.fetchMe()
  const [memberRes, shipRes] = await Promise.allSettled([
    getMemberStatus(),
    getShippingOrders(),
  ])
  memberStatus.value = memberRes.status === 'fulfilled' ? memberRes.value : null
  shippingOrders.value = shipRes.status === 'fulfilled' ? shipRes.value : []
}

onShow(() => load())

function go(path: string) {
  uni.navigateTo({ url: path })
}

function goLogin() {
  uni.navigateTo({ url: '/pages/auth/login' })
}

function logout() {
  userStore.logout()
  uni.showToast({ title: '已退出', icon: 'none' })
}
</script>

<template>
  <view class="page container">
    <view v-if="userStore.isLoggedIn" class="card profile">
      <text class="name">{{ userStore.user?.nickname || userStore.user?.username }}</text>
      <text class="meta">
        {{ memberStatus?.is_vip ? '会员 · 至 ' + (memberStatus?.expire_time || '') : '普通用户' }}
      </text>
    </view>
    <view v-else class="card" @tap="goLogin">
      <text>点击登录 / 注册</text>
    </view>

    <view class="menu card">
      <view class="menu-item" @tap="go('/pages/user/orders')">我的订单</view>
      <view class="menu-item" @tap="go('/pages/user/favorites')">我的收藏</view>
      <view class="menu-item" @tap="go('/pages/user/history')">浏览记录</view>
      <view class="menu-item" @tap="go('/pages/member/index')">会员中心</view>
    </view>

    <view v-if="shippingOrders.length" class="card">
      <text class="section-title">收发货追踪</text>
      <view v-for="o in shippingOrders.slice(0, 3)" :key="o.id" class="ship-item">
        <text>{{ o.order_no }} · {{ o.status_label || o.status }}</text>
        <text v-if="o.ship_tracking_no" class="track">物流：{{ o.ship_company }} {{ o.ship_tracking_no }}</text>
      </view>
    </view>

    <button v-if="userStore.isLoggedIn" class="logout" @tap="logout">退出登录</button>
  </view>
</template>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.name {
  display: block;
  font-size: 36rpx;
  font-weight: 700;
}

.meta {
  display: block;
  margin-top: 8rpx;
  color: $color-text-secondary;
}

.menu-item {
  padding: 24rpx 0;
  border-bottom: 1rpx solid #eee;
}

.menu-item:last-child {
  border-bottom: none;
}

.section-title {
  display: block;
  font-weight: 600;
  margin-bottom: 16rpx;
}

.ship-item {
  padding: 12rpx 0;
  font-size: 26rpx;
}

.track {
  display: block;
  color: $color-text-secondary;
  font-size: 22rpx;
  margin-top: 4rpx;
}

.logout {
  margin-top: 40rpx;
  background: #fff;
  color: $color-text-secondary;
}
</style>
