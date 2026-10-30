<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { request } from '@/api/client'
import BookReviewVideosUpload from '@/components/admin/BookReviewVideosUpload.vue'

interface BookOption {
  id: number
  title: string
}

interface VideoGroupRow {
  book_id: number
  book_title: string
  video_count: number
  video_url: string
  play_count: number
  status: number
  videos: Array<{ video_url: string }>
}

const groups = ref<VideoGroupRow[]>([])
const books = ref<BookOption[]>([])
const dialog = ref(false)
const saving = ref(false)
const editingBookId = ref<number | null>(null)
const formBookId = ref<number | null>(null)
const videoUrls = ref<string[]>([])
const formStatus = ref(1)

const bookMap = computed(() => Object.fromEntries(books.value.map((b) => [b.id, b.title])))

async function loadBooks() {
  const res = await request<BookOption[]>({ url: '/admin/books' })
  if (res.code === 200) {
    books.value = (res.data || []).map((item: any) => ({
      id: item.id,
      title: item.title,
    }))
  }
}

async function load() {
  const res = await request<VideoGroupRow[]>({ url: '/admin/videos' })
  if (res.code === 200) groups.value = res.data || []
}

function openCreate() {
  editingBookId.value = null
  formBookId.value = books.value[0]?.id ?? null
  videoUrls.value = []
  formStatus.value = 1
  dialog.value = true
}

async function openEdit(row: VideoGroupRow) {
  editingBookId.value = row.book_id
  formBookId.value = row.book_id
  formStatus.value = row.status ?? 1
  const res = await request<Array<{ video_url: string; status?: number }>>({
    url: `/admin/videos/by-book/${row.book_id}`,
  })
  if (res.code === 200) {
    videoUrls.value = (res.data || []).map((item) => item.video_url)
    if (res.data?.[0]?.status != null) {
      formStatus.value = res.data[0].status ?? 1
    }
  } else {
    videoUrls.value = row.videos?.map((item) => item.video_url) || []
  }
  dialog.value = true
}

async function save() {
  if (!formBookId.value) {
    ElMessage.warning('请选择书籍')
    return
  }

  saving.value = true
  try {
    const res = await request({
      url: `/admin/videos/by-book/${formBookId.value}`,
      method: 'PUT',
      data: {
        videos: videoUrls.value.map((url) => ({
          video_url: url,
          video_cover: '',
          video_duration: 0,
          video_intro: '',
          status: formStatus.value,
        })),
      },
    })
    if (res.code === 200) {
      ElMessage.success('解读视频已保存')
      dialog.value = false
      await load()
    } else {
      ElMessage.error(res.msg || '保存失败')
    }
  } finally {
    saving.value = false
  }
}

async function removeGroup(row: VideoGroupRow) {
  if (!confirm(`确定删除《${row.book_title || row.book_id}》的全部解读视频？`)) return
  const res = await request({
    url: `/admin/videos/by-book/${row.book_id}`,
    method: 'PUT',
    data: { videos: [] },
  })
  if (res.code === 200) {
    ElMessage.success('已删除')
    await load()
  } else {
    ElMessage.error(res.msg || '删除失败')
  }
}

onMounted(async () => {
  await loadBooks()
  await load()
})
</script>

<template>
  <div class="page-card">
    <div class="page-header">
      <div>
        <h2>解读视频管理</h2>
        <p class="subtitle">每本书可绑定多条解读视频，按顺序自动连播</p>
      </div>
      <el-button type="primary" @click="openCreate">+ 绑定视频</el-button>
    </div>

    <el-table :data="groups">
      <el-table-column prop="book_id" label="书籍ID" width="80" />
      <el-table-column label="书名" min-width="160">
        <template #default="{ row }">{{ row.book_title || bookMap[row.book_id] || '-' }}</template>
      </el-table-column>
      <el-table-column prop="video_count" label="视频数" width="80" />
      <el-table-column prop="video_url" label="首条视频" show-overflow-tooltip />
      <el-table-column prop="play_count" label="播放量" width="80" />
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">{{ row.status === 1 ? '上架' : '下架' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">管理视频</el-button>
          <el-button size="small" type="danger" @click="removeGroup(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialog"
      :title="editingBookId ? `管理解读视频 · 书籍 #${editingBookId}` : '绑定解读视频'"
      width="720px"
      destroy-on-close
    >
      <el-form label-width="100px">
        <el-form-item label="选择书籍">
          <el-select
            v-model="formBookId"
            placeholder="请选择书籍"
            filterable
            :disabled="!!editingBookId"
            style="width: 100%"
          >
            <el-option
              v-for="book in books"
              :key="book.id"
              :label="`${book.title} (#${book.id})`"
              :value="book.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="解读视频">
          <BookReviewVideosUpload v-model="videoUrls" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="formStatus">
            <el-option :value="1" label="上架" />
            <el-option :value="0" label="下架" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.subtitle {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
</style>
