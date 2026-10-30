<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  DataAnalysis,
  Film,
  Reading,
  ShoppingCart,
  User,
} from '@element-plus/icons-vue'
import { fetchDashboardOverview, type DashboardOverview } from '@/api/adminStats'
import { formatBeijingTime } from '@/utils/datetime'
import { placeholderCover, resolveMediaUrl } from '@/utils/media'

const router = useRouter()
const loading = ref(true)
const data = ref<DashboardOverview | null>(null)

const statCards = computed(() => {
  const s = data.value?.summary
  if (!s) return []
  return [
    {
      key: 'books',
      label: '图书总数',
      value: s.books.total,
      foot: `上架 ${s.books.published} · 草稿 ${s.books.draft}`,
      icon: Reading,
      tone: 'blue',
      link: '/admin/book/list',
    },
    {
      key: 'users',
      label: '注册用户',
      value: s.users.total,
      foot: `今日新增 ${s.users.today}`,
      icon: User,
      tone: 'green',
      link: '/admin/permission/user',
    },
    {
      key: 'orders',
      label: '今日成交额',
      value: `¥${formatMoney(s.orders.today_amount)}`,
      foot: `今日订单 ${s.orders.today_count} · 累计 ¥${formatMoney(s.orders.total_amount)}`,
      icon: ShoppingCart,
      tone: 'orange',
      link: '/admin/order/all',
    },
    {
      key: 'videos',
      label: '视频总播放',
      value: formatNumber(s.videos.play_count),
      foot: `解读视频 ${s.videos.total} 部 · 收藏 ${s.collects.total}`,
      icon: Film,
      tone: 'purple',
      link: '/admin/content/video',
    },
  ]
})

const bookStatusBars = computed(() => {
  const status = data.value?.book_status
  if (!status) return []
  const total = Math.max(status.published + status.draft, 1)
  return [
    { label: '已上架', value: status.published, color: '#5d87ff', ratio: (status.published / total) * 100 },
    { label: '草稿', value: status.draft, color: '#c9cdd4', ratio: (status.draft / total) * 100 },
  ]
})

const categoryBars = computed(() => {
  const list = data.value?.category_distribution || []
  const max = Math.max(...list.map((item) => item.count), 1)
  return list.map((item) => ({
    ...item,
    ratio: (item.count / max) * 100,
  }))
})

const orderTrendChart = computed(() => buildTrendChart(data.value?.order_trend || [], 'count'))
const userTrendChart = computed(() => buildTrendChart(data.value?.user_trend || [], 'count'))

const weekOrderTotal = computed(() =>
  (data.value?.order_trend || []).reduce((sum, item) => sum + item.count, 0),
)
const weekUserTotal = computed(() =>
  (data.value?.user_trend || []).reduce((sum, item) => sum + item.count, 0),
)

onMounted(async () => {
  loading.value = true
  try {
    const res = await fetchDashboardOverview()
    if (res.code === 200) data.value = res.data
  } finally {
    loading.value = false
  }
})

function formatNumber(value: number) {
  return value.toLocaleString('zh-CN')
}

function formatMoney(value: number) {
  return value.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

function formatShortDate(iso: string) {
  const [, month, day] = iso.split('-')
  return `${month}/${day}`
}

function formatDateTime(iso: string | null) {
  return formatBeijingTime(iso)
}

function bookCover(cover: string, id: number) {
  return resolveMediaUrl(cover, id)
}

function statusTagType(status: string) {
  if (status === 'completed') return 'success'
  if (status === 'cancelled') return 'info'
  if (status === 'pending_payment') return 'warning'
  return 'primary'
}

function go(path: string) {
  router.push(path)
}

function buildTrendChart(points: { date: string; count: number }[], key: 'count') {
  const width = 360
  const height = 140
  const padding = { top: 16, right: 12, bottom: 28, left: 12 }
  const innerW = width - padding.left - padding.right
  const innerH = height - padding.top - padding.bottom
  const values = points.map((p) => p[key])
  const max = Math.max(...values, 1)

  const coords = points.map((point, index) => {
    const x = padding.left + (index / Math.max(points.length - 1, 1)) * innerW
    const y = padding.top + innerH - (point[key] / max) * innerH
    return { x, y, ...point }
  })

  const line = coords.map((c) => `${c.x},${c.y}`).join(' ')
  const area = [
    `M ${coords[0]?.x ?? padding.left} ${padding.top + innerH}`,
    ...coords.map((c) => `L ${c.x} ${c.y}`),
    `L ${coords[coords.length - 1]?.x ?? padding.left} ${padding.top + innerH}`,
    'Z',
  ].join(' ')

  return { width, height, coords, line, area, max }
}
</script>

<template>
  <div v-loading="loading" class="dashboard-page">
    <div class="dashboard-hero">
      <div class="hero-copy">
        <div class="hero-badge">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据分析</span>
        </div>
        <h1>全站总览仪表盘</h1>
        <p>汇总图书、用户、订单与视频播放等核心业务指标，辅助日常运营决策。</p>
      </div>
      <div v-if="data" class="hero-meta">
        <div class="meta-item">
          <span class="meta-label">有效会员</span>
          <strong>{{ data.summary.members.vip_active }}</strong>
        </div>
        <div class="meta-item">
          <span class="meta-label">每日读书</span>
          <strong>{{ data.summary.daily.total }} 期</strong>
        </div>
        <div class="meta-item">
          <span class="meta-label">今日收藏</span>
          <strong>{{ data.summary.collects.today }}</strong>
        </div>
      </div>
    </div>

    <div class="stat-grid">
      <button
        v-for="card in statCards"
        :key="card.key"
        type="button"
        class="stat-card"
        :class="`tone-${card.tone}`"
        @click="go(card.link)"
      >
        <div class="stat-icon">
          <el-icon :size="22"><component :is="card.icon" /></el-icon>
        </div>
        <div class="stat-body">
          <span class="stat-label">{{ card.label }}</span>
          <strong class="stat-value">{{ card.value }}</strong>
          <span class="stat-foot">{{ card.foot }}</span>
        </div>
      </button>
    </div>

    <div class="chart-grid">
      <section class="panel-card">
        <div class="panel-header">
          <div>
            <h3>图书状态分布</h3>
            <p>按上架与草稿状态统计当前书库结构</p>
          </div>
        </div>
        <div class="bar-chart">
          <div v-for="bar in bookStatusBars" :key="bar.label" class="bar-row">
            <span class="bar-label">{{ bar.label }}</span>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: `${bar.ratio}%`, background: bar.color }" />
            </div>
            <span class="bar-value">{{ bar.value }}</span>
          </div>
        </div>
      </section>

      <section class="panel-card">
        <div class="panel-header">
          <div>
            <h3>近 7 日订单趋势</h3>
            <p>本周新增订单 {{ weekOrderTotal }} 笔</p>
          </div>
        </div>
        <svg
          class="trend-chart"
          :viewBox="`0 0 ${orderTrendChart.width} ${orderTrendChart.height}`"
          preserveAspectRatio="none"
        >
          <defs>
            <linearGradient id="orderArea" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="rgba(93, 135, 255, 0.35)" />
              <stop offset="100%" stop-color="rgba(93, 135, 255, 0.02)" />
            </linearGradient>
          </defs>
          <path :d="orderTrendChart.area" fill="url(#orderArea)" />
          <polyline :points="orderTrendChart.line" fill="none" stroke="#5d87ff" stroke-width="2.5" />
          <circle
            v-for="point in orderTrendChart.coords"
            :key="point.date"
            :cx="point.x"
            :cy="point.y"
            r="3.5"
            fill="#fff"
            stroke="#5d87ff"
            stroke-width="2"
          />
        </svg>
        <div class="trend-axis">
          <span v-for="point in data?.order_trend || []" :key="point.date">
            {{ formatShortDate(point.date) }}
          </span>
        </div>
      </section>

      <section class="panel-card">
        <div class="panel-header">
          <div>
            <h3>分类图书占比</h3>
            <p>各分类下图书数量对比</p>
          </div>
        </div>
        <div v-if="categoryBars.length" class="category-list">
          <div v-for="item in categoryBars" :key="item.name" class="category-row">
            <span class="category-name">{{ item.name }}</span>
            <div class="category-track">
              <div class="category-fill" :style="{ width: `${item.ratio}%` }" />
            </div>
            <span class="category-count">{{ item.count }}</span>
          </div>
        </div>
        <el-empty v-else description="暂无分类数据" :image-size="72" />
      </section>
    </div>

    <div class="table-grid">
      <section class="panel-card">
        <div class="panel-header">
          <div>
            <h3>最近订单</h3>
            <p>最新 5 条图书交易记录</p>
          </div>
          <el-button type="primary" link @click="go('/admin/order/all')">查看全部</el-button>
        </div>
        <el-table
          v-if="data?.recent_orders.length"
          :data="data.recent_orders"
          size="small"
          class="dashboard-table"
        >
          <el-table-column label="订单号" prop="order_no" min-width="150" />
          <el-table-column label="用户" prop="user_nickname" width="90" />
          <el-table-column label="商品" prop="book_summary" min-width="140" show-overflow-tooltip />
          <el-table-column label="金额" width="90">
            <template #default="{ row }">¥{{ formatMoney(row.total_amount) }}</template>
          </el-table-column>
          <el-table-column label="状态" width="88">
            <template #default="{ row }">
              <el-tag :type="statusTagType(row.status)" size="small" effect="plain">
                {{ row.status_label }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="时间" width="120">
            <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无订单，可在前台下单后查看" :image-size="80" />
      </section>

      <section class="panel-card">
        <div class="panel-header">
          <div>
            <h3>热门书籍</h3>
            <p>按浏览量排行 TOP 5</p>
          </div>
          <el-button type="primary" link @click="go('/admin/book/list')">管理书籍</el-button>
        </div>
        <div v-if="data?.top_books.length" class="book-list">
          <div v-for="book in data.top_books" :key="book.id" class="book-item">
            <img
              :src="bookCover(book.cover, book.id)"
              :alt="book.title"
              class="book-cover"
              @error="($event.target as HTMLImageElement).src = placeholderCover(book.id)"
            />
            <div class="book-copy">
              <span class="book-title">{{ book.title }}</span>
              <span class="book-meta">
                浏览 {{ formatNumber(book.view_count) }} · 播放 {{ formatNumber(book.play_count) }}
              </span>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无图书数据" :image-size="80" />
      </section>
    </div>

    <section class="panel-card trend-secondary">
      <div class="panel-header">
        <div>
          <h3>近 7 日新增用户</h3>
          <p>本周新注册 {{ weekUserTotal }} 人</p>
        </div>
      </div>
      <svg
        class="trend-chart wide"
        :viewBox="`0 0 ${userTrendChart.width} ${userTrendChart.height}`"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="userArea" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="rgba(45, 106, 79, 0.28)" />
            <stop offset="100%" stop-color="rgba(45, 106, 79, 0.02)" />
          </linearGradient>
        </defs>
        <path :d="userTrendChart.area" fill="url(#userArea)" />
        <polyline :points="userTrendChart.line" fill="none" stroke="#2d6a4f" stroke-width="2.5" />
      </svg>
      <div class="trend-axis">
        <span v-for="point in data?.user_trend || []" :key="point.date">
          {{ formatShortDate(point.date) }}
        </span>
      </div>
    </section>
  </div>
</template>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-height: 100%;
}

.dashboard-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 22px 24px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(93, 135, 255, 0.12), rgba(124, 58, 237, 0.08));
  border: 1px solid rgba(93, 135, 255, 0.14);
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  color: var(--ecms-primary);
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 10px;
}

.hero-copy h1 {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 700;
  color: var(--ecms-text);
}

.hero-copy p {
  margin: 0;
  color: var(--ecms-text-secondary);
  line-height: 1.6;
  max-width: 560px;
}

.hero-meta {
  display: flex;
  gap: 14px;
  flex-shrink: 0;
}

.meta-item {
  min-width: 96px;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(93, 135, 255, 0.12);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.meta-label {
  font-size: 12px;
  color: var(--ecms-text-secondary);
}

.meta-item strong {
  font-size: 18px;
  color: var(--ecms-text);
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.stat-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 18px;
  border-radius: 14px;
  border: 1px solid var(--ecms-border);
  background: var(--ecms-card-bg);
  box-shadow: var(--ecms-shadow);
  text-align: left;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
  font-family: inherit;
}

.stat-card:hover {
  transform: translateY(-2px);
  border-color: rgba(93, 135, 255, 0.28);
  box-shadow: 0 10px 24px rgba(93, 135, 255, 0.12);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.tone-blue .stat-icon {
  background: rgba(93, 135, 255, 0.12);
  color: #5d87ff;
}

.tone-green .stat-icon {
  background: rgba(45, 106, 79, 0.12);
  color: #2d6a4f;
}

.tone-orange .stat-icon {
  background: rgba(247, 127, 0, 0.12);
  color: #f77f00;
}

.tone-purple .stat-icon {
  background: rgba(124, 58, 237, 0.12);
  color: #7c3aed;
}

.stat-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.stat-label {
  font-size: 13px;
  color: var(--ecms-text-secondary);
}

.stat-value {
  font-size: 26px;
  line-height: 1.2;
  color: var(--ecms-text);
}

.stat-foot {
  font-size: 12px;
  color: var(--ecms-text-secondary);
  line-height: 1.5;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.table-grid {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 14px;
}

.panel-card {
  padding: 18px 18px 16px;
  border-radius: 14px;
  border: 1px solid var(--ecms-border);
  background: var(--ecms-card-bg);
  box-shadow: var(--ecms-shadow);
}

.trend-secondary {
  margin-top: 0;
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.panel-header h3 {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 600;
  color: var(--ecms-text);
}

.panel-header p {
  margin: 0;
  font-size: 12px;
  color: var(--ecms-text-secondary);
}

.bar-chart,
.category-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.bar-row,
.category-row {
  display: grid;
  grid-template-columns: 56px 1fr 36px;
  align-items: center;
  gap: 10px;
}

.bar-label,
.category-name,
.bar-value,
.category-count {
  font-size: 13px;
  color: var(--ecms-text-secondary);
}

.bar-track,
.category-track {
  height: 10px;
  border-radius: 999px;
  background: #eef2ff;
  overflow: hidden;
}

.bar-fill,
.category-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #5d87ff, #7c3aed);
}

.trend-chart {
  width: 100%;
  height: 140px;
  display: block;
}

.trend-chart.wide {
  height: 120px;
}

.trend-axis {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  margin-top: 8px;
  font-size: 11px;
  color: var(--ecms-text-secondary);
  text-align: center;
}

.dashboard-table :deep(.el-table__header th) {
  background: #f7f9ff;
  color: var(--ecms-text-secondary);
  font-weight: 600;
}

.book-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.book-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  background: #f8faff;
  border: 1px solid rgba(93, 135, 255, 0.08);
}

.book-cover {
  width: 42px;
  height: 56px;
  border-radius: 8px;
  object-fit: cover;
  flex-shrink: 0;
  background: #eef2ff;
}

.book-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.book-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ecms-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.book-meta {
  font-size: 12px;
  color: var(--ecms-text-secondary);
}

@media (max-width: 1280px) {
  .stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .chart-grid {
    grid-template-columns: 1fr;
  }

  .table-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dashboard-hero {
    flex-direction: column;
  }

  .hero-meta {
    width: 100%;
    flex-wrap: wrap;
  }

  .stat-grid {
    grid-template-columns: 1fr;
  }
}
</style>
