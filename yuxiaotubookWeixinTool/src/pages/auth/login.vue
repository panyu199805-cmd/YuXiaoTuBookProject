<script setup lang="ts">
import { onLoad } from '@dcloudio/uni-app'
import { ref } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const form = ref({ username: '', password: '' })
const redirect = ref('/pages/index/index')
const loading = ref(false)
const error = ref('')

onLoad((query) => {
  if (query?.redirect) redirect.value = decodeURIComponent(String(query.redirect))
})

async function submit() {
  error.value = ''
  if (!form.value.username || !form.value.password) {
    error.value = '请填写用户名和密码'
    return
  }
  loading.value = true
  try {
    await userStore.login(form.value.username, form.value.password)
    uni.showToast({ title: '登录成功', icon: 'success' })
    setTimeout(() => {
      if (redirect.value.startsWith('/pages/')) {
        const tabPages = ['/pages/index/index', '/pages/books/list', '/pages/daily/index', '/pages/user/center']
        if (tabPages.includes(redirect.value.split('?')[0])) {
          uni.switchTab({ url: redirect.value.split('?')[0] })
        } else {
          uni.redirectTo({ url: redirect.value })
        }
      } else {
        uni.switchTab({ url: '/pages/index/index' })
      }
    }, 500)
  } catch (e: any) {
    error.value = e?.message || '登录失败'
  } finally {
    loading.value = false
  }
}

function goRegister() {
  uni.navigateTo({ url: '/pages/auth/register' })
}
</script>

<template>
  <view class="page container auth">
    <text class="title">登录宇小兔读书</text>
    <input v-model="form.username" class="input" placeholder="用户名" />
    <input v-model="form.password" class="input" password placeholder="密码" />
    <text v-if="error" class="error">{{ error }}</text>
    <button class="btn-primary" :loading="loading" @tap="submit">登录</button>
    <text class="link" @tap="goRegister">没有账号？去注册</text>
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

.btn-primary {
  margin-top: 12rpx;
}

.link {
  display: block;
  text-align: center;
  margin-top: 32rpx;
  color: $color-primary;
}
</style>
