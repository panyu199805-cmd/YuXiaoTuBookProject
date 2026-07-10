<script setup lang="ts">
import { ref } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const form = ref({
  username: '',
  password: '',
  nickname: '',
})
const loading = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  if (!form.value.username || !form.value.password) {
    error.value = '请填写用户名和密码'
    return
  }
  loading.value = true
  try {
    await userStore.register({
      username: form.value.username,
      password: form.value.password,
      nickname: form.value.nickname || form.value.username,
    })
    uni.showToast({ title: '注册成功', icon: 'success' })
    setTimeout(() => uni.switchTab({ url: '/pages/index/index' }), 500)
  } catch (e: any) {
    error.value = e?.message || '注册失败'
  } finally {
    loading.value = false
  }
}

function goLogin() {
  uni.navigateBack()
}
</script>

<template>
  <view class="page container auth">
    <text class="title">注册账号</text>
    <input v-model="form.username" class="input" placeholder="用户名（4-20位）" />
    <input v-model="form.password" class="input" password placeholder="密码（至少8位）" />
    <input v-model="form.nickname" class="input" placeholder="昵称（可选）" />
    <text v-if="error" class="error">{{ error }}</text>
    <button class="btn-primary" :loading="loading" @tap="submit">注册</button>
    <text class="link" @tap="goLogin">已有账号？去登录</text>
  </view>
</template>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.auth {
  padding-top: 80rpx;
}

.title {
  display: block;
  font-size: 40rpx;
  font-weight: 700;
  margin-bottom: 40rpx;
}

.input {
  background: $color-surface;
  border-radius: 12rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}

.error {
  color: #c44536;
  font-size: 24rpx;
  margin-bottom: 16rpx;
  display: block;
}

.link {
  display: block;
  text-align: center;
  margin-top: 32rpx;
  color: $color-primary;
}
</style>
