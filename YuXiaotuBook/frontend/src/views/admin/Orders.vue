<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { request } from '@/api/client'
import { formatBeijingTime } from '@/utils/datetime'

const orders = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const pageSizes = [10, 20, 30, 40, 50]
const loading = ref(false)
const shipDialog = ref(false)
const shipForm = ref({ order_id: 0, ship_company: '', ship_tracking_no: '' })
const shipping = ref(false)
const detailVisible = ref(false)
const detailOrder = ref<any>(null)
const cancelDialog = ref(false)
const cancelSubmitting = ref(false)
const cancelForm = ref({ order_id: 0, reason: '', custom_reason: '' })
const editDialog = ref(false)
const editSubmitting = ref(false)
const editForm = ref({
  order_id: 0,
  order_no: '',
  status: '',
  status_label: '',
  book_name: '',
  total_amount: 0,
  receiver_name: '',
  receiver_phone: '',
  receiver_address: '',
  ship_company: '',
  ship_tracking_no: '',
  show_logistics: false,
})

const cancelReasonOptions = [
  '用户主动取消',
  '缺货无法发货',
  '地址信息有误',
  '重复下单',
  '其他',
]

const filters = ref({
  order_no: '',
  book_name: '',
  user_nickname: '',
  receiver_phone: '',
  ship_tracking_no: '',
  status: '',
  created_range: [] as string[],
  pay_range: [] as string[],
})

const statusOptions = [
  { label: '待支付', value: 'pending_payment' },
  { label: '待发货', value: 'paid' },
  { label: '运输中', value: 'shipped' },
  { label: '已完成', value: 'completed' },
  { label: '已取消', value: 'cancelled' },
]

function formatTime(value?: string | null) {
  return formatBeijingTime(value)
}

function formatAmount(value?: number | null) {
  if (value == null) return '—'
  return `¥${Number(value).toFixed(2)}`
}

function cancelByLabel(value?: string | null) {
  if (value === 'admin') return '管理员'
  if (value === 'user') return '用户'
  return '—'
}

function statusTagType(status: string) {
  const map: Record<string, string> = {
    pending_payment: 'info',
    paid: 'warning',
    shipped: '',
    completed: 'success',
    cancelled: 'info',
  }
  return map[status] || 'info'
}

function hasStateActions(row: any) {
  return ['paid', 'pending_payment', 'shipped'].includes(row.status)
}

function buildQueryParams() {
  const params: Record<string, string | number> = {
    page: page.value,
    page_size: pageSize.value,
  }
  const f = filters.value
  if (f.order_no.trim()) params.order_no = f.order_no.trim()
  if (f.book_name.trim()) params.book_name = f.book_name.trim()
  if (f.user_nickname.trim()) params.user_nickname = f.user_nickname.trim()
  if (f.receiver_phone.trim()) params.receiver_phone = f.receiver_phone.trim()
  if (f.ship_tracking_no.trim()) params.ship_tracking_no = f.ship_tracking_no.trim()
  if (f.status) params.status = f.status
  if (f.created_range?.length === 2) {
    params.created_start = f.created_range[0]
    params.created_end = f.created_range[1]
  }
  if (f.pay_range?.length === 2) {
    params.pay_start = f.pay_range[0]
    params.pay_end = f.pay_range[1]
  }
  return params
}

async function load() {
  loading.value = true
  try {
    const res = await request<{ list: any[]; total: number }>({
      url: '/admin/orders',
      params: buildQueryParams(),
    })
    if (res.code === 200 && res.data) {
      orders.value = res.data.list || []
      total.value = res.data.total || 0
    }
  } finally {
    loading.value = false
  }
}

function search() {
  page.value = 1
  load()
}

function resetFilters() {
  filters.value = {
    order_no: '',
    book_name: '',
    user_nickname: '',
    receiver_phone: '',
    ship_tracking_no: '',
    status: '',
    created_range: [],
    pay_range: [],
  }
  page.value = 1
  load()
}

function onPageChange(nextPage: number) {
  page.value = nextPage
  load()
}

function onSizeChange(nextSize: number) {
  pageSize.value = nextSize
  page.value = 1
  load()
}

function openDetail(row: any) {
  detailOrder.value = row
  detailVisible.value = true
}

function canEdit(row: any) {
  return row.status !== 'cancelled'
}

function openEdit(row: any) {
  editForm.value = {
    order_id: row.id,
    order_no: row.order_no,
    status: row.status,
    status_label: row.status_label,
    book_name: row.book_name || '',
    total_amount: row.total_amount,
    receiver_name: row.receiver_name || '',
    receiver_phone: row.receiver_phone || '',
    receiver_address: row.receiver_address || '',
    ship_company: row.ship_company || '',
    ship_tracking_no: row.ship_tracking_no || '',
    show_logistics: ['paid', 'shipped', 'completed'].includes(row.status),
  }
  editDialog.value = true
}

async function submitEdit() {
  const form = editForm.value
  if (!form.receiver_name.trim() || !form.receiver_phone.trim() || !form.receiver_address.trim()) {
    alert('请完整填写收货信息')
    return
  }
  editSubmitting.value = true
  try {
    const res = await request({
      url: `/admin/orders/${form.order_id}`,
      method: 'PUT',
      data: {
        receiver_name: form.receiver_name.trim(),
        receiver_phone: form.receiver_phone.trim(),
        receiver_address: form.receiver_address.trim(),
        ship_company: form.show_logistics ? form.ship_company.trim() || null : null,
        ship_tracking_no: form.show_logistics ? form.ship_tracking_no.trim() || null : null,
      },
    })
    if (res.code === 200) {
      editDialog.value = false
      if (detailOrder.value?.id === form.order_id) {
        detailOrder.value = res.data
      }
      load()
    } else {
      alert(res.msg || '保存失败')
    }
  } finally {
    editSubmitting.value = false
  }
}

function openCancel(row: any) {
  cancelForm.value = { order_id: row.id, reason: '', custom_reason: '' }
  cancelDialog.value = true
}

async function submitCancel() {
  const reason =
    cancelForm.value.reason === '其他'
      ? cancelForm.value.custom_reason.trim()
      : cancelForm.value.reason
  if (!reason) {
    alert('请填写或选择取消原因')
    return
  }
  cancelSubmitting.value = true
  try {
    const res = await request({
      url: `/admin/orders/${cancelForm.value.order_id}/status`,
      method: 'PUT',
      params: { status: 'cancelled', cancel_reason: reason },
    })
    if (res.code === 200) {
      cancelDialog.value = false
      if (detailOrder.value?.id === cancelForm.value.order_id) {
        detailOrder.value = res.data
      }
      load()
    } else {
      alert(res.msg || '取消失败')
    }
  } finally {
    cancelSubmitting.value = false
  }
}

function openShip(row: any) {
  shipForm.value = { order_id: row.id, ship_company: '顺丰速运', ship_tracking_no: '' }
  shipDialog.value = true
}

async function submitShip() {
  if (!shipForm.value.ship_tracking_no.trim()) {
    alert('请填写运单号')
    return
  }
  shipping.value = true
  try {
    const res = await request({
      url: `/admin/orders/${shipForm.value.order_id}/ship`,
      method: 'PUT',
      data: {
        ship_company: shipForm.value.ship_company,
        ship_tracking_no: shipForm.value.ship_tracking_no,
      },
    })
    if (res.code === 200) {
      shipDialog.value = false
      if (detailOrder.value?.id === shipForm.value.order_id) {
        detailOrder.value = res.data
      }
      load()
    } else {
      alert(res.msg)
    }
  } finally {
    shipping.value = false
  }
}

async function complete(id: number) {
  const res = await request({ url: `/admin/orders/${id}/status`, method: 'PUT', params: { status: 'completed' } })
  if (res.code === 200) {
    if (detailOrder.value?.id === id) {
      detailOrder.value = res.data
    }
    load()
  } else {
    alert(res.msg || '操作失败')
  }
}

onMounted(load)
</script>

<template>
  <div class="page-card orders-page">
    <div class="page-header">
      <h2>订单管理</h2>
      <span class="total-hint">共 {{ total }} 条订单</span>
    </div>

    <div class="filter-panel">
      <el-form :model="filters" label-width="72px" @submit.prevent="search">
        <el-row :gutter="16">
          <el-col :xs="24" :sm="12" :md="8" :lg="6">
            <el-form-item label="订单号">
              <el-input v-model="filters.order_no" clearable placeholder="订单号" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8" :lg="6">
            <el-form-item label="图书名称">
              <el-input v-model="filters.book_name" clearable placeholder="图书名称" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8" :lg="6">
            <el-form-item label="用户昵称">
              <el-input v-model="filters.user_nickname" clearable placeholder="用户昵称" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8" :lg="6">
            <el-form-item label="收货手机">
              <el-input v-model="filters.receiver_phone" clearable placeholder="收货手机号" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8" :lg="6">
            <el-form-item label="运单号">
              <el-input v-model="filters.ship_tracking_no" clearable placeholder="物流运单号" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8" :lg="6">
            <el-form-item label="状态">
              <el-select v-model="filters.status" clearable placeholder="全部" style="width: 100%">
                <el-option
                  v-for="item in statusOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="24" :md="12" :lg="6">
            <el-form-item label="下单时间">
              <el-date-picker
                v-model="filters.created_range"
                type="daterange"
                range-separator="至"
                start-placeholder="开始"
                end-placeholder="结束"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="24" :md="12" :lg="6">
            <el-form-item label="支付时间">
              <el-date-picker
                v-model="filters.pay_range"
                type="daterange"
                range-separator="至"
                start-placeholder="开始"
                end-placeholder="结束"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <div class="filter-actions">
          <el-button type="primary" @click="search">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </div>
      </el-form>
    </div>

    <el-table
      v-loading="loading"
      class="orders-table"
      :data="orders"
      row-key="id"
      stripe
      border
      size="small"
    >
      <el-table-column prop="order_no" label="订单号" min-width="172" fixed="left">
        <template #default="{ row }">
          <span class="order-no">{{ row.order_no }}</span>
        </template>
      </el-table-column>

      <el-table-column label="图书名称" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">{{ row.book_name || '—' }}</template>
      </el-table-column>

      <el-table-column label="数量" width="64" align="center">
        <template #default="{ row }">{{ row.total_quantity ?? '—' }}</template>
      </el-table-column>

      <el-table-column label="用户昵称" min-width="96" show-overflow-tooltip>
        <template #default="{ row }">
          <span>{{ row.user_nickname || row.username || '—' }}</span>
        </template>
      </el-table-column>

      <el-table-column label="状态" width="88" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" size="small" effect="light">
            {{ row.status_label }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="金额" width="88" align="right">
        <template #default="{ row }">
          <span class="amount">{{ formatAmount(row.total_amount) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="收货人" min-width="116">
        <template #default="{ row }">
          <div class="cell-stack">
            <span>{{ row.receiver_name || '—' }}</span>
            <span v-if="row.receiver_phone" class="sub">{{ row.receiver_phone }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="物流" min-width="132" show-overflow-tooltip>
        <template #default="{ row }">
          <div v-if="row.ship_tracking_no" class="cell-stack">
            <span>{{ row.ship_company }}</span>
            <span class="sub">{{ row.ship_tracking_no }}</span>
          </div>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>

      <el-table-column label="下单时间" min-width="148">
        <template #default="{ row }">
          <span class="time-text">{{ formatTime(row.created_at) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="148" fixed="right" align="center">
        <template #default="{ row }">
          <div class="table-actions">
            <div class="action-row">
              <el-button size="small" link type="primary" @click="openDetail(row)">详情</el-button>
              <el-button
                v-if="canEdit(row)"
                size="small"
                link
                type="primary"
                @click="openEdit(row)"
              >编辑</el-button>
            </div>
            <div v-if="hasStateActions(row)" class="action-row">
              <template v-if="row.status === 'paid'">
                <el-button size="small" link type="primary" @click="openShip(row)">发货</el-button>
                <el-button size="small" link type="danger" @click="openCancel(row)">取消</el-button>
              </template>
              <template v-else-if="row.status === 'pending_payment'">
                <el-button size="small" link type="danger" @click="openCancel(row)">取消</el-button>
              </template>
              <template v-else-if="row.status === 'shipped'">
                <el-button size="small" link type="success" @click="complete(row.id)">完结</el-button>
              </template>
            </div>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrap">
      <el-pagination
        :current-page="page"
        :page-size="pageSize"
        :page-sizes="pageSizes"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @current-change="onPageChange"
        @size-change="onSizeChange"
      />
    </div>

    <el-drawer v-model="detailVisible" title="订单详情" size="480px">
      <template v-if="detailOrder">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="订单号">{{ detailOrder.order_no }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ detailOrder.status_label }}</el-descriptions-item>
          <el-descriptions-item label="用户">
            {{ detailOrder.user_nickname || detailOrder.username || '—' }}
            <span v-if="detailOrder.user_id" class="muted">（ID: {{ detailOrder.user_id }}）</span>
          </el-descriptions-item>
          <el-descriptions-item label="订单金额">{{ formatAmount(detailOrder.total_amount) }}</el-descriptions-item>
          <el-descriptions-item label="下单时间">{{ formatTime(detailOrder.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="支付时间">{{ formatTime(detailOrder.pay_time) }}</el-descriptions-item>
          <el-descriptions-item label="发货时间">{{ formatTime(detailOrder.shipped_at) }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">{{ formatTime(detailOrder.completed_at) }}</el-descriptions-item>
          <el-descriptions-item v-if="detailOrder.status === 'cancelled'" label="取消时间">
            {{ formatTime(detailOrder.cancelled_at) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="detailOrder.status === 'cancelled'" label="取消方">
            {{ cancelByLabel(detailOrder.cancel_by) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="detailOrder.cancel_reason" label="取消原因">
            {{ detailOrder.cancel_reason }}
          </el-descriptions-item>
        </el-descriptions>

        <h4 class="detail-section-title">商品明细</h4>
        <el-table :data="detailOrder.items || []" size="small" border>
          <el-table-column prop="book_title" label="书名" min-width="160" show-overflow-tooltip />
          <el-table-column prop="price" label="单价" width="90" align="right">
            <template #default="{ row }">{{ formatAmount(row.price) }}</template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="70" align="center" />
          <el-table-column label="小计" width="90" align="right">
            <template #default="{ row }">{{ formatAmount(row.price * row.quantity) }}</template>
          </el-table-column>
        </el-table>

        <h4 class="detail-section-title">收货信息</h4>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="收货人">{{ detailOrder.receiver_name || '—' }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ detailOrder.receiver_phone || '—' }}</el-descriptions-item>
          <el-descriptions-item label="收货地址">{{ detailOrder.receiver_address || '—' }}</el-descriptions-item>
        </el-descriptions>

        <h4 class="detail-section-title">物流信息</h4>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="快递公司">{{ detailOrder.ship_company || '—' }}</el-descriptions-item>
          <el-descriptions-item label="运单号">{{ detailOrder.ship_tracking_no || '—' }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-drawer>

    <el-dialog v-model="editDialog" title="编辑订单" width="520px">
      <el-form label-width="88px">
        <el-form-item label="订单号">
          <el-input :model-value="editForm.order_no" disabled />
        </el-form-item>
        <el-form-item label="状态">
          <el-input :model-value="editForm.status_label" disabled />
        </el-form-item>
        <el-form-item label="图书">
          <el-input :model-value="editForm.book_name" disabled />
        </el-form-item>
        <el-form-item label="金额">
          <el-input :model-value="formatAmount(editForm.total_amount)" disabled />
        </el-form-item>
        <el-divider content-position="left">收货信息</el-divider>
        <el-form-item label="收货人" required>
          <el-input v-model="editForm.receiver_name" placeholder="收货人姓名" />
        </el-form-item>
        <el-form-item label="联系电话" required>
          <el-input v-model="editForm.receiver_phone" placeholder="手机号" />
        </el-form-item>
        <el-form-item label="收货地址" required>
          <el-input
            v-model="editForm.receiver_address"
            type="textarea"
            :rows="3"
            placeholder="省市区 + 详细地址"
          />
        </el-form-item>
        <template v-if="editForm.show_logistics">
          <el-divider content-position="left">物流信息</el-divider>
          <el-form-item label="快递公司">
            <el-input v-model="editForm.ship_company" placeholder="如：顺丰速运" />
          </el-form-item>
          <el-form-item label="运单号">
            <el-input v-model="editForm.ship_tracking_no" placeholder="物流运单号" />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="editDialog = false">取消</el-button>
        <el-button type="primary" :loading="editSubmitting" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="cancelDialog" title="取消订单" width="440px">
      <el-form label-width="88px">
        <el-form-item label="取消原因" required>
          <el-select v-model="cancelForm.reason" placeholder="请选择原因" style="width: 100%">
            <el-option v-for="item in cancelReasonOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="cancelForm.reason === '其他'" label="详细说明" required>
          <el-input
            v-model="cancelForm.custom_reason"
            type="textarea"
            :rows="3"
            placeholder="请填写取消原因"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cancelDialog = false">返回</el-button>
        <el-button type="danger" :loading="cancelSubmitting" @click="submitCancel">确认取消</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="shipDialog" title="订单发货" width="420px">
      <el-form label-width="80px">
        <el-form-item label="快递公司">
          <el-input v-model="shipForm.ship_company" placeholder="如：顺丰速运" />
        </el-form-item>
        <el-form-item label="运单号">
          <el-input v-model="shipForm.ship_tracking_no" placeholder="请输入运单号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shipDialog = false">取消</el-button>
        <el-button type="primary" :loading="shipping" @click="submitShip">确认发货</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.orders-page .page-header {
  margin-bottom: 12px;
}

.total-hint {
  font-size: 13px;
  color: var(--ecms-text-secondary, #86909c);
}

.filter-panel {
  margin-bottom: 16px;
  padding: 16px 16px 4px;
  background: #f7f8fa;
  border: 1px solid var(--ecms-border, #e5e6eb);
  border-radius: var(--ecms-radius, 8px);
}

.filter-panel :deep(.el-form-item) {
  margin-bottom: 12px;
}

.filter-panel :deep(.el-form-item__label) {
  color: #4e5969;
}

.filter-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-bottom: 12px;
}

.orders-table {
  width: 100%;
}

.orders-table :deep(.el-table__header th) {
  background: #f7f8fa;
  color: #4e5969;
  font-weight: 600;
}

.order-no {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
  letter-spacing: -0.2px;
}

.amount {
  font-variant-numeric: tabular-nums;
  font-weight: 500;
}

.time-text {
  font-size: 12px;
  color: #4e5969;
  white-space: nowrap;
}

.cell-stack {
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1.35;
}

.detail-section-title {
  margin: 20px 0 12px;
  font-size: 15px;
  font-weight: 600;
}

.muted {
  color: #999;
}

.sub {
  font-size: 12px;
  color: #909399;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.table-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 4px 12px;
}

.table-actions :deep(.el-button.is-link) {
  padding: 0;
  margin: 0;
  height: auto;
  font-size: 13px;
}
</style>
