<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { request } from '@/api/client'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const store = useUserStore()
const packages = ref<any[]>([])
const status = ref<any>(null)
const loading = ref(false)

async function load() {
  const res = await request<any[]>({ url: '/member/packages' })
  if (res.code === 200) packages.value = res.data
  if (store.isLoggedIn) {
    const s = await request<any>({ url: '/member/status' })
    if (s.code === 200) {
      status.value = s.data
    }
  }
}

async function subscribe(packageId: number) {
  if (!store.isLoggedIn) {
    router.push({ name: 'Login', query: { redirect: '/member' } })
    return
  }
  loading.value = true
  try {
    const order = await request<any>({
      url: '/member/subscribe',
      method: 'POST',
      data: { package_id: packageId },
    })
    if (order.code !== 200) {
      alert(order.msg)
      return
    }
    const pay = await request({
      url: `/member/orders/${order.data.id}/mock-pay`,
      method: 'POST',
    })
    if (pay.code === 200) {
      alert('会员开通成功')
      await store.fetchMe()
      load()
    } else {
      alert(pay.msg)
    }
  } finally {
    loading.value = false
  }
}

function parseRights(raw: string | string[]) {
  if (Array.isArray(raw)) return raw
  try {
    return JSON.parse(raw || '[]')
  } catch {
    return []
  }
}

onMounted(load)
</script>

<template>
  <div class="container page">
    <h1 class="page-title">会员中心</h1>

    <div v-if="status?.is_vip" class="vip-banner">
      当前为会员，有效期至 {{ status.expire_time?.slice(0, 10) }}
    </div>

    <div class="grid">
      <div v-for="pkg in packages" :key="pkg.id" class="pkg-card">
        <h3>{{ pkg.package_name }}</h3>
        <p class="price">¥{{ pkg.price }} / {{ pkg.valid_day }} 天</p>
        <ul>
          <li v-for="(r, i) in parseRights(pkg.rights)" :key="i">{{ r }}</li>
        </ul>
        <button class="btn btn-primary" :disabled="loading" @click="subscribe(pkg.id)">
          立即开通
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 32px 20px 48px; }
.vip-banner {
  background: linear-gradient(135deg, #5d87ff, #7c3aed);
  color: #fff;
  padding: 16px 20px;
  border-radius: var(--radius-card);
  margin-bottom: 24px;
}
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
.pkg-card {
  background: var(--color-surface);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  padding: 24px;
}
.price { font-size: 24px; color: var(--color-primary); margin: 12px 0; font-weight: 600; }
ul { margin: 16px 0 20px; padding-left: 20px; color: var(--color-text-secondary); }
li { margin-bottom: 6px; }

@media (max-width: 1023px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 767px) {
  .page { padding: 24px 12px 40px; }
  .grid { grid-template-columns: 1fr; }
  .pkg-card { padding: 20px 16px; }
  .price { font-size: 20px; }
}
</style>
