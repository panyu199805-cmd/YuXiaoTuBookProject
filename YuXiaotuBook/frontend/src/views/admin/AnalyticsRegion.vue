<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { fetchRegionStats, type RegionStats } from '@/api/adminStats'
import { buildBarRatios, formatMoney, formatNumber } from '@/composables/useAnalyticsCharts'

const loading = ref(true)
const data = ref<RegionStats | null>(null)

const provinceBars = computed(() =>
  buildBarRatios((data.value?.province_stats || []).map((item) => ({
    ...item,
    count: item.user_count,
  }))),
)
const cityBars = computed(() =>
  buildBarRatios(
    (data.value?.city_stats || []).map((item) => ({
      ...item,
      count: item.user_count,
    })),
  ),
)

onMounted(async () => {
  loading.value = true
  try {
    const res = await fetchRegionStats()
    if (res.code === 200) data.value = res.data
  } finally {
    loading.value = false
  }
})

function formatTopCategories(categories: { name: string; count: number }[]) {
  return categories.map((c) => `${c.name}(${c.count})`).join('、')
}
</script>

<template>
  <div v-loading="loading" class="analytics-page">
    <header class="page-hero">
      <div>
        <h1>用户地域分布分析</h1>
        <p>基于用户注册资料中的省/市信息，结合订单与阅读偏好做地域洞察。</p>
      </div>
    </header>

    <div v-if="data" class="stat-grid">
      <div class="stat-card"><span>覆盖省份</span><strong>{{ data.summary.province_count }}</strong></div>
      <div class="stat-card"><span>注册用户</span><strong>{{ formatNumber(data.summary.user_total) }}</strong></div>
      <div class="stat-card"><span>已填地域</span><strong>{{ formatNumber(data.summary.filled_region_users) }}</strong></div>
      <div class="stat-card"><span>未填地域</span><strong>{{ formatNumber(data.summary.user_total - data.summary.filled_region_users) }}</strong></div>
    </div>

    <div class="panel-grid">
      <section class="panel-card span-2">
        <div class="panel-header"><h3>省份用户分布</h3><p>各省注册用户数对比</p></div>
        <div class="bar-list">
          <div v-for="item in provinceBars" :key="item.province" class="bar-row province-row">
            <span>{{ item.province }}</span>
            <div class="bar-track"><div class="bar-fill" :style="{ width: `${item.ratio}%` }" /></div>
            <em>{{ item.user_count }}</em>
          </div>
        </div>
      </section>

      <section class="panel-card">
        <div class="panel-header"><h3>城市 TOP10</h3><p>注册用户数最多的城市</p></div>
        <div class="bar-list">
          <div v-for="item in cityBars" :key="item.city" class="bar-row city-row">
            <span>{{ item.city }}</span>
            <div class="bar-track"><div class="bar-fill city" :style="{ width: `${item.ratio}%` }" /></div>
            <em>{{ item.user_count }}</em>
          </div>
        </div>
      </section>

      <section class="panel-card span-2">
        <div class="panel-header"><h3>省份订单与偏好</h3><p>各省订单量、成交额及偏好分类</p></div>
        <el-table :data="data?.province_stats || []" size="small">
          <el-table-column label="省份" prop="province" width="120" />
          <el-table-column label="用户数" prop="user_count" width="90" />
          <el-table-column label="订单数" prop="order_count" width="90" />
          <el-table-column label="成交额" width="110">
            <template #default="{ row }">¥{{ formatMoney(row.order_amount) }}</template>
          </el-table-column>
          <el-table-column label="偏好分类" min-width="180">
            <template #default="{ row }">
              <span v-if="row.top_categories.length">
                {{ formatTopCategories(row.top_categories) }}
              </span>
              <span v-else>—</span>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </div>
  </div>
</template>

<style scoped>
@import './analytics-shared.css';

.bar-row span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.province-row {
  grid-template-columns: 88px 1fr 40px;
}

.city-row {
  grid-template-columns: 120px 1fr 40px;
}

.bar-fill.city {
  background: linear-gradient(90deg, #2d6a4f, #95d5b2);
}
</style>
