<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'
import {
  getMemberPackages,
  getMemberStatus,
  mockPayMemberOrder,
  subscribeMember,
} from '@/api/trade'
import EmptyState from '@/components/EmptyState.vue'
import { useUserStore } from '@/stores/user'
import type { MemberPackage, MemberStatus } from '@/types/user'

const userStore = useUserStore()
const packages = ref<MemberPackage[]>([])
const status = ref<MemberStatus | null>(null)
const loading = ref(false)

function parseRights(raw: string[] | string) {
  if (Array.isArray(raw)) return raw
  try {
    return JSON.parse(raw || '[]') as string[]
  } catch {
    return []
  }
}

async function load() {
  packages.value = await getMemberPackages()
  if (userStore.isLoggedIn) {
    status.value = await getMemberStatus()
  } else {
    status.value = null
  }
}

onShow(() => load())

async function subscribe(packageId: number) {
  if (!userStore.isLoggedIn) {
    uni.navigateTo({ url: '/pages/auth/login?redirect=' + encodeURIComponent('/pages/member/index') })
    return
  }
  loading.value = true
  try {
    const order = await subscribeMember(packageId)
    await mockPayMemberOrder(order.id)
    uni.showToast({ title: '会员开通成功', icon: 'success' })
    await userStore.fetchMe()
    await load()
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <view class="page container">
    <view v-if="status?.is_vip" class="card vip-banner">
      <text>当前已是会员</text>
      <text class="expire">有效期至 {{ status.expire_time || '—' }}</text>
    </view>

    <view v-for="pkg in packages" :key="pkg.id" class="card pkg">
      <text class="name">{{ pkg.package_name }}</text>
      <text class="price">¥{{ pkg.price }} / {{ pkg.valid_day }} 天</text>
      <view v-for="(r, i) in parseRights(pkg.rights)" :key="i" class="right">· {{ r }}</view>
      <button class="btn-primary" :loading="loading" @tap="subscribe(pkg.id)">立即开通</button>
    </view>
    <EmptyState v-if="!packages.length" text="暂无会员套餐" />
  </view>
</template>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.vip-banner {
  background: linear-gradient(135deg, $color-primary, $color-primary-dark);
  color: #fff;
}

.expire {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  opacity: 0.9;
}

.name {
  display: block;
  font-size: 32rpx;
  font-weight: 600;
}

.price {
  display: block;
  margin: 12rpx 0;
  color: $color-primary;
  font-size: 28rpx;
}

.right {
  font-size: 24rpx;
  color: $color-text-secondary;
  margin-bottom: 6rpx;
}

.btn-primary {
  margin-top: 20rpx;
}
</style>
