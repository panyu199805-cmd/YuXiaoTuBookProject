<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { request } from '@/api/client'

const orders = ref<any[]>([])

onMounted(async () => {
  const res = await request<any[]>({ url: '/orders' })
  if (res.code === 200) orders.value = res.data
})
</script>

<template>
  <div class="container page">
    <h1 class="page-title">我的订单</h1>
    <div v-for="o in orders" :key="o.id" class="order-card">
      <div class="head">
        <span>{{ o.order_no }}</span>
        <span class="status">{{ o.status }}</span>
      </div>
      <p v-for="item in o.items" :key="item.book_id">{{ item.book_title }} x{{ item.quantity }}</p>
      <p class="amount">¥{{ o.total_amount?.toFixed(2) }}</p>
    </div>
    <p v-if="!orders.length" class="empty">暂无订单</p>
  </div>
</template>

<style scoped>
.page { padding-top: 32px; }
.order-card {
  background: var(--color-surface);
  padding: 16px 20px;
  border-radius: var(--radius-card);
  margin-bottom: 12px;
  box-shadow: var(--shadow-card);
}
.head { display: flex; justify-content: space-between; margin-bottom: 8px; }
.status { color: var(--color-primary); }
.amount { margin-top: 8px; font-weight: 600; }
.empty { text-align: center; color: var(--color-text-secondary); }

@media (max-width: 767px) {
  .page { padding: 24px 12px 40px; }
  .order-card { padding: 14px 16px; }
  .head { flex-direction: column; gap: 4px; }
}
</style>
