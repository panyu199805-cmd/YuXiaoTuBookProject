<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { request } from '@/api/client'
import { useUserStore } from '@/stores/user'

const store = useUserStore()

const categories = ref<{ id: number; name: string }[]>([])
const prefs = ref({ category_ids: [] as number[], scene_tags: [] as string[], bio: '' })
const shippingOrders = ref<any[]>([])
const shippingTab = ref<'all' | 'paid' | 'shipped' | 'completed'>('all')
const saving = ref(false)
const memberStatus = ref<any>(null)

const sceneOptions = [
  { value: 'commute', label: '通勤' },
  { value: 'before_sleep', label: '睡前' },
  { value: 'weekend', label: '周末深度' },
  { value: 'career', label: '职场充电' },
]

const filteredOrders = computed(() => {
  if (shippingTab.value === 'all') return shippingOrders.value
  return shippingOrders.value.filter((o) => o.status === shippingTab.value)
})

async function load() {
  await store.fetchMe()
  const [cats, pref, ship, member] = await Promise.all([
    request<any[]>({ url: '/categories' }),
    request<any>({ url: '/user/preferences' }),
    request<any[]>({ url: '/user/orders/shipping' }),
    request<any>({ url: '/member/status' }),
  ])
  if (cats.code === 200) categories.value = cats.data
  if (pref.code === 200) {
    prefs.value = {
      category_ids: pref.data.category_ids || [],
      scene_tags: pref.data.scene_tags || [],
      bio: pref.data.bio || '',
    }
  }
  if (ship.code === 200) shippingOrders.value = ship.data
  if (member.code === 200) memberStatus.value = member.data
}

function toggleCategory(id: number) {
  const idx = prefs.value.category_ids.indexOf(id)
  if (idx >= 0) {
    prefs.value.category_ids.splice(idx, 1)
    return
  }
  if (prefs.value.category_ids.length >= 8) {
    alert('最多选择 8 个分类')
    return
  }
  prefs.value.category_ids.push(id)
}

function toggleScene(value: string) {
  const idx = prefs.value.scene_tags.indexOf(value)
  if (idx >= 0) prefs.value.scene_tags.splice(idx, 1)
  else prefs.value.scene_tags.push(value)
}

async function savePrefs() {
  saving.value = true
  try {
    const res = await request({
      url: '/user/preferences',
      method: 'PUT',
      data: prefs.value,
    })
    if (res.code === 200) alert('喜好已保存')
    else alert(res.msg)
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="container page">
    <h1 class="page-title">个人中心</h1>

    <section class="card overview">
      <div class="profile">
        <div class="avatar">{{ store.user?.nickname?.[0] || '读' }}</div>
        <div>
          <h2>{{ store.user?.nickname || store.user?.username }}</h2>
          <p class="sub">@{{ store.user?.username }}</p>
          <p v-if="memberStatus?.is_vip" class="vip-line">
            会员有效期至 {{ memberStatus.expire_time?.slice(0, 10) }}
          </p>
          <p v-else class="sub">开通会员解锁更多权益</p>
        </div>
      </div>
      <div class="quick-links">
        <router-link to="/user/favorites">收藏</router-link>
        <router-link to="/user/history">浏览记录</router-link>
        <router-link to="/member">会员中心</router-link>
        <router-link to="/user/orders">全部订单</router-link>
      </div>
    </section>

    <section class="card">
      <h3>读书喜好私人订制</h3>
      <p class="hint">选择你感兴趣的分类（最多 8 个），我们将为你优化推荐</p>
      <div class="tag-grid">
        <button
          v-for="c in categories"
          :key="c.id"
          type="button"
          class="tag"
          :class="{ active: prefs.category_ids.includes(c.id) }"
          @click="toggleCategory(c.id)"
        >
          {{ c.name }}
        </button>
      </div>

      <p class="label">阅读场景</p>
      <div class="tag-grid">
        <button
          v-for="s in sceneOptions"
          :key="s.value"
          type="button"
          class="tag"
          :class="{ active: prefs.scene_tags.includes(s.value) }"
          @click="toggleScene(s.value)"
        >
          {{ s.label }}
        </button>
      </div>

      <p class="label">一句话简介</p>
      <textarea v-model="prefs.bio" class="bio" maxlength="100" placeholder="例如：喜欢心理学和治愈类短阅读" />
      <button class="btn btn-primary save-btn" :disabled="saving" @click="savePrefs">保存喜好</button>
    </section>

    <section class="card">
      <h3>已购书籍收发货</h3>
      <div class="tabs">
        <button :class="{ active: shippingTab === 'all' }" @click="shippingTab = 'all'">全部</button>
        <button :class="{ active: shippingTab === 'paid' }" @click="shippingTab = 'paid'">待发货</button>
        <button :class="{ active: shippingTab === 'shipped' }" @click="shippingTab = 'shipped'">运输中</button>
        <button :class="{ active: shippingTab === 'completed' }" @click="shippingTab = 'completed'">已完成</button>
      </div>

      <div v-for="o in filteredOrders" :key="o.id" class="ship-card" :class="{ muted: o.status === 'cancelled' }">
        <div class="ship-head">
          <span class="status">{{ o.status_label }}</span>
          <span class="no">{{ o.order_no }}</span>
        </div>
        <p v-for="item in o.items" :key="item.book_id" class="item-line">
          {{ item.book_title }} × {{ item.quantity }}
        </p>
        <p class="amount">¥{{ o.total_amount?.toFixed(2) }}</p>
        <p v-if="o.status === 'shipped'" class="logistics">
          {{ o.ship_company }} · {{ o.ship_tracking_no }}
          <span v-if="o.shipped_at"> · 发货 {{ o.shipped_at.slice(0, 10) }}</span>
        </p>
        <p v-if="o.receiver_address" class="addr">收货：{{ o.receiver_name }} {{ o.receiver_address }}</p>
      </div>

      <p v-if="!filteredOrders.length" class="empty">
        暂无相关记录，<router-link to="/books">去书单逛逛</router-link>
      </p>
    </section>
  </div>
</template>

<style scoped>
.page { padding: 32px 20px 48px; }
.card {
  background: var(--color-surface);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  padding: 24px;
  margin-bottom: 20px;
}
.overview .profile { display: flex; gap: 16px; align-items: center; margin-bottom: 16px; }
.avatar {
  width: 56px; height: 56px; border-radius: 50%;
  background: linear-gradient(135deg, #5d87ff, #7c3aed);
  color: #fff; display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 600;
}
.profile h2 { font-size: 20px; margin-bottom: 4px; }
.sub { color: var(--color-text-secondary); font-size: 14px; }
.vip-line { color: var(--color-primary); font-size: 14px; margin-top: 4px; }
.quick-links { display: flex; flex-wrap: wrap; gap: 12px; }
.quick-links a {
  padding: 6px 14px; border-radius: 20px; background: var(--color-bg);
  font-size: 13px; color: var(--color-text);
}
.card h3 { margin-bottom: 8px; font-size: 18px; }
.hint, .label { color: var(--color-text-secondary); font-size: 13px; margin: 12px 0 8px; }
.tag-grid { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 8px; }
.tag {
  border: 1px solid var(--color-border); background: #fff; padding: 6px 14px;
  border-radius: 20px; cursor: pointer; font-size: 13px;
}
.tag.active { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }
.bio {
  width: 100%; min-height: 72px; padding: 10px 12px; border: 1px solid var(--color-border);
  border-radius: 8px; resize: vertical; font-family: inherit;
}
.save-btn { margin-top: 12px; }
.tabs { display: flex; gap: 8px; margin: 16px 0; flex-wrap: wrap; }
.tabs button {
  border: none; background: var(--color-bg); padding: 6px 14px; border-radius: 16px;
  cursor: pointer; font-size: 13px;
}
.tabs button.active { background: var(--color-primary); color: #fff; }
.ship-card {
  border: 1px solid var(--color-border); border-radius: 10px; padding: 14px 16px; margin-bottom: 12px;
}
.ship-card.muted { opacity: 0.6; }
.ship-head { display: flex; justify-content: space-between; margin-bottom: 8px; }
.status { color: var(--color-primary); font-weight: 600; }
.no { color: var(--color-text-secondary); font-size: 12px; }
.item-line { font-size: 14px; margin-bottom: 4px; }
.amount { font-weight: 600; margin-top: 6px; }
.logistics, .addr { font-size: 13px; color: var(--color-text-secondary); margin-top: 6px; }
.empty { text-align: center; color: var(--color-text-secondary); padding: 24px 0; }

@media (max-width: 767px) {
  .page { padding: 24px 12px 40px; }
  .card { padding: 16px; }
  .overview .profile { flex-direction: column; align-items: flex-start; }
  .ship-head { flex-direction: column; gap: 4px; }
  .tabs { gap: 4px; }
  .tabs button { font-size: 12px; padding: 4px 10px; }
  .quick-links { gap: 8px; }
  .quick-links a { font-size: 12px; padding: 4px 10px; }
}
</style>
