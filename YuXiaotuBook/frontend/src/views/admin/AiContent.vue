<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  acceptAiItem,
  discardAiItem,
  fetchAiConfig,
  fetchAiTasks,
  generateAiContent,
  updateAiItem,
  type AiContentItem,
  type AiContentTask,
  type AiContentType,
  type AiRuntimeConfig,
} from '@/api/adminAi'
import { request } from '@/api/client'
import { resolveMediaUrl } from '@/utils/media'

interface BookOption {
  id: number
  title: string
  author: string
  cover: string
}

const loading = ref(false)
const generating = ref(false)
const books = ref<BookOption[]>([])
const config = ref<AiRuntimeConfig | null>(null)
const activeTab = ref<'result' | 'history'>('result')
const currentTask = ref<AiContentTask | null>(null)
const history = ref<AiContentTask[]>([])
const drawerVisible = ref(false)
const activeItem = ref<AiContentItem | null>(null)
const draftText = ref('')
const publishDate = ref(new Date().toISOString().slice(0, 10))
const accepting = ref(false)

const form = ref({
  book_ids: [] as number[],
  content_types: ['book_summary', 'book_highlight'] as AiContentType[],
  tone: 'healing',
  length: 'medium',
  extra_prompt: '',
  write_mode: 'empty_only' as 'empty_only' | 'overwrite',
})

const modeTag = computed(() => {
  const mode = config.value?.mode
  if (mode === 'live') return { type: 'success' as const, text: `在线 · ${config.value?.model}` }
  if (mode === 'mock') return { type: 'warning' as const, text: 'Mock 模式（未配置 API Key）' }
  return { type: 'info' as const, text: '未开通' }
})

const typeOptions = computed(() => config.value?.content_types || [])

const resultItems = computed(() => currentTask.value?.items || [])

async function loadBooks() {
  const res = await request<BookOption[]>({ url: '/admin/books' })
  if (res.code === 200) books.value = res.data || []
}

async function loadConfig() {
  const res = await fetchAiConfig()
  if (res.code === 200) config.value = res.data
}

async function loadHistory() {
  const res = await fetchAiTasks(20)
  if (res.code === 200) history.value = res.data || []
}

async function onGenerate() {
  if (!form.value.book_ids.length) {
    ElMessage.warning('请先选择书籍')
    return
  }
  if (!form.value.content_types.length) {
    ElMessage.warning('请选择至少一种生成类型')
    return
  }
  if (config.value?.mode === 'disabled') {
    ElMessage.error('未配置 AI_API_KEY，且 Mock 已关闭')
    return
  }

  generating.value = true
  try {
    const res = await generateAiContent({
      book_ids: form.value.book_ids,
      content_types: form.value.content_types,
      tone: form.value.tone,
      length: form.value.length,
      extra_prompt: form.value.extra_prompt || undefined,
      write_mode: form.value.write_mode,
    })
    if (res.code !== 200) {
      ElMessage.error(res.msg || '生成失败')
      return
    }
    currentTask.value = res.data
    activeTab.value = 'result'
    ElMessage.success(res.msg || '生成完成')
    await loadHistory()
  } catch (err: any) {
    ElMessage.error(err?.message || '生成请求失败')
  } finally {
    generating.value = false
  }
}

function openItem(item: AiContentItem) {
  activeItem.value = item
  draftText.value = item.edited_text || item.generated_text || ''
  drawerVisible.value = true
}

async function saveDraft() {
  if (!activeItem.value) return
  const res = await updateAiItem(activeItem.value.id, draftText.value)
  if (res.code !== 200) {
    ElMessage.error(res.msg || '保存失败')
    return
  }
  patchItem(res.data)
  ElMessage.success('已保存编辑')
}

async function onAccept() {
  if (!activeItem.value) return
  const item = activeItem.value
  const needsDate = item.content_type === 'daily_sentence' || item.content_type === 'daily_intro'
  if (item.content_type === 'reading_note') {
    ElMessage.info('读书笔记仅作草稿，请复制使用，不支持写入业务表')
    return
  }
  if (needsDate && !publishDate.value) {
    ElMessage.warning('请选择每日专栏发布日期')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确认将「${item.content_type_label}」写入 ${item.target_field}？`,
      '采纳入库',
      { type: 'warning' },
    )
  } catch {
    return
  }

  accepting.value = true
  try {
    const res = await acceptAiItem(item.id, {
      text: draftText.value,
      write_mode: form.value.write_mode,
      publish_date: needsDate ? publishDate.value : undefined,
    })
    if (res.code !== 200) {
      ElMessage.error(res.msg || '采纳失败')
      return
    }
    patchItem(res.data)
    activeItem.value = res.data
    ElMessage.success('已采纳入库')
    drawerVisible.value = false
  } finally {
    accepting.value = false
  }
}

async function onDiscard(item?: AiContentItem) {
  const target = item || activeItem.value
  if (!target) return
  try {
    await ElMessageBox.confirm('确定丢弃该条生成结果？', '提示', { type: 'warning' })
  } catch {
    return
  }
  const res = await discardAiItem(target.id)
  if (res.code !== 200) {
    ElMessage.error(res.msg || '操作失败')
    return
  }
  patchItem(res.data)
  if (activeItem.value?.id === target.id) drawerVisible.value = false
  ElMessage.success('已丢弃')
}

function patchItem(updated: AiContentItem) {
  if (currentTask.value) {
    currentTask.value = {
      ...currentTask.value,
      items: currentTask.value.items.map((row) => (row.id === updated.id ? updated : row)),
    }
  }
  history.value = history.value.map((task) => ({
    ...task,
    items: task.items.map((row) => (row.id === updated.id ? updated : row)),
  }))
  if (activeItem.value?.id === updated.id) activeItem.value = updated
}

function openHistoryTask(task: AiContentTask) {
  currentTask.value = task
  activeTab.value = 'result'
}

function statusType(status: string) {
  if (status === 'accepted') return 'success'
  if (status === 'discarded' || status === 'failed') return 'info'
  if (status === 'draft') return 'warning'
  return 'primary'
}

function coverOf(item: AiContentItem) {
  return resolveMediaUrl(item.book_cover, item.book_id)
}

onMounted(async () => {
  loading.value = true
  try {
    await Promise.all([loadConfig(), loadBooks(), loadHistory()])
    if (history.value.length) currentTask.value = history.value[0]
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="ai-page" v-loading="loading">
    <div class="ai-grid">
      <section class="page-card config-panel">
        <div class="panel-head">
          <div>
            <h2>AI 内容生成</h2>
            <p class="sub">选书 → 生成 → 校对 → 采纳入库。未配置 Key 时自动 Mock，便于联调。</p>
          </div>
          <el-tag :type="modeTag.type" effect="plain">{{ modeTag.text }}</el-tag>
        </div>

        <el-form label-position="top" class="ai-form">
          <el-form-item label="选择书籍（最多 10 本）">
            <el-select
              v-model="form.book_ids"
              multiple
              filterable
              collapse-tags
              collapse-tags-tooltip
              placeholder="搜索书名"
              style="width: 100%"
              :multiple-limit="10"
            >
              <el-option
                v-for="book in books"
                :key="book.id"
                :label="`${book.title} · ${book.author}`"
                :value="book.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="生成类型">
            <el-checkbox-group v-model="form.content_types" class="type-group">
              <el-checkbox
                v-for="opt in typeOptions"
                :key="opt.value"
                :value="opt.value"
                :label="opt.value"
              >
                {{ opt.label }}
              </el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <div class="row-2">
            <el-form-item label="语气">
              <el-select v-model="form.tone" style="width: 100%">
                <el-option label="治愈温柔" value="healing" />
                <el-option label="专业理性" value="professional" />
                <el-option label="口语亲切" value="casual" />
              </el-select>
            </el-form-item>
            <el-form-item label="篇幅">
              <el-select v-model="form.length" style="width: 100%">
                <el-option label="偏短" value="short" />
                <el-option label="适中" value="medium" />
                <el-option label="偏长" value="long" />
              </el-select>
            </el-form-item>
          </div>

          <el-form-item label="写入策略（采纳时生效）">
            <el-radio-group v-model="form.write_mode">
              <el-radio value="empty_only">仅空字段写入</el-radio>
              <el-radio value="overwrite">允许覆盖已有内容</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="补充提示词（可选）">
            <el-input
              v-model="form.extra_prompt"
              type="textarea"
              :rows="3"
              maxlength="500"
              show-word-limit
              placeholder="例如：面向职场新人，避免鸡汤腔"
            />
          </el-form-item>

          <el-button
            type="primary"
            size="large"
            :loading="generating"
            :disabled="config?.mode === 'disabled'"
            style="width: 100%"
            @click="onGenerate"
          >
            开始生成
          </el-button>
        </el-form>
      </section>

      <section class="page-card result-panel">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="本次 / 选中结果" name="result">
            <div v-if="!resultItems.length" class="empty">生成结果会显示在这里</div>
            <div v-else class="item-list">
              <article
                v-for="item in resultItems"
                :key="item.id"
                class="item-card"
                @click="openItem(item)"
              >
                <img class="cover" :src="coverOf(item)" :alt="item.book_title || ''" />
                <div class="item-body">
                  <div class="item-title-row">
                    <strong>{{ item.book_title || `书籍#${item.book_id}` }}</strong>
                    <el-tag size="small" :type="statusType(item.status)">{{ item.status }}</el-tag>
                  </div>
                  <div class="meta">{{ item.content_type_label }} · {{ item.target_field }}</div>
                  <p class="preview">{{ item.final_text || item.error_message || '—' }}</p>
                </div>
              </article>
            </div>
          </el-tab-pane>

          <el-tab-pane label="历史任务" name="history">
            <div v-if="!history.length" class="empty">暂无历史任务</div>
            <div v-else class="history-list">
              <button
                v-for="task in history"
                :key="task.id"
                type="button"
                class="history-row"
                @click="openHistoryTask(task)"
              >
                <div>
                  <strong>#{{ task.id }}</strong>
                  <span class="meta"> · {{ task.created_at }} · {{ task.provider_mode }}</span>
                </div>
                <div class="meta">
                  {{ task.book_ids.length }} 本书 · {{ task.items.length }} 条 · {{ task.status }}
                </div>
              </button>
            </div>
          </el-tab-pane>
        </el-tabs>
      </section>
    </div>

    <el-drawer
      v-model="drawerVisible"
      size="520px"
      :title="activeItem ? `${activeItem.content_type_label} · ${activeItem.book_title || ''}` : '校对'"
    >
      <template v-if="activeItem">
        <p class="drawer-meta">目标字段：{{ activeItem.target_field }}</p>

        <div class="compare-block" v-if="activeItem.source_text">
          <h4>原文</h4>
          <p class="source">{{ activeItem.source_text }}</p>
        </div>

        <div class="compare-block">
          <h4>AI 文案（可编辑）</h4>
          <el-input v-model="draftText" type="textarea" :rows="12" />
        </div>

        <div
          class="compare-block"
          v-if="activeItem.content_type === 'daily_sentence' || activeItem.content_type === 'daily_intro'"
        >
          <h4>写入每日专栏日期</h4>
          <el-date-picker
            v-model="publishDate"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            style="width: 100%"
          />
        </div>

        <div class="drawer-actions">
          <el-button @click="saveDraft" :disabled="activeItem.status === 'accepted'">保存编辑</el-button>
          <el-button
            type="primary"
            :loading="accepting"
            :disabled="activeItem.status === 'accepted' || activeItem.status === 'discarded'"
            @click="onAccept"
          >
            采纳入库
          </el-button>
          <el-button
            type="danger"
            plain
            :disabled="activeItem.status === 'accepted' || activeItem.status === 'discarded'"
            @click="onDiscard()"
          >
            丢弃
          </el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<style scoped>
.ai-page {
  min-height: 100%;
}

.ai-grid {
  display: grid;
  grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.panel-head h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.sub {
  margin: 6px 0 0;
  color: var(--ecms-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.ai-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.type-group {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 12px;
}

.row-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.empty {
  padding: 48px 12px;
  text-align: center;
  color: var(--ecms-text-secondary);
}

.item-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.item-card {
  display: grid;
  grid-template-columns: 56px 1fr;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--ecms-border);
  border-radius: 10px;
  cursor: pointer;
  background: #fff;
  transition: border-color 0.15s ease;
}

.item-card:hover {
  border-color: rgba(93, 135, 255, 0.45);
}

.cover {
  width: 56px;
  height: 76px;
  object-fit: cover;
  border-radius: 6px;
  background: #f0f2f5;
}

.item-title-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.meta {
  margin-top: 4px;
  color: var(--ecms-text-secondary);
  font-size: 12px;
}

.preview {
  margin: 8px 0 0;
  color: var(--ecms-text);
  font-size: 13px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-row {
  text-align: left;
  border: 1px solid var(--ecms-border);
  border-radius: 10px;
  padding: 12px;
  background: #fff;
  cursor: pointer;
}

.history-row:hover {
  border-color: rgba(93, 135, 255, 0.45);
}

.drawer-meta {
  margin: 0 0 12px;
  color: var(--ecms-text-secondary);
  font-size: 13px;
}

.compare-block {
  margin-bottom: 16px;
}

.compare-block h4 {
  margin: 0 0 8px;
  font-size: 13px;
  color: var(--ecms-text-secondary);
  font-weight: 600;
}

.source {
  margin: 0;
  padding: 10px 12px;
  background: rgba(93, 135, 255, 0.06);
  border-radius: 8px;
  line-height: 1.7;
  white-space: pre-wrap;
  font-size: 13px;
}

.drawer-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

@media (max-width: 960px) {
  .ai-grid {
    grid-template-columns: 1fr;
  }
}
</style>
