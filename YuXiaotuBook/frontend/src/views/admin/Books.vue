<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { request } from '@/api/client'
import CoverUpload from '@/components/admin/CoverUpload.vue'

const books = ref<any[]>([])
const categories = ref<any[]>([])
const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = ref({
  title: '',
  author: '',
  cover: '',
  category_id: 1,
  price: 0,
  stock: 0,
  summary: '',
  highlight: '',
  status: 'published',
})

const emptyForm = () => ({
  title: '',
  author: '',
  cover: '',
  category_id: categories.value[0]?.id ?? 1,
  price: 0,
  stock: 0,
  summary: '',
  highlight: '',
  status: 'published',
})

async function load() {
  const [b, c] = await Promise.all([
    request<any[]>({ url: '/admin/books' }),
    request({ url: '/admin/categories' }),
  ])
  if (b.code === 200) books.value = b.data ?? []
  if (c.code === 200) categories.value = (c.data as any[]) ?? []
}

function openCreate() {
  editingId.value = null
  form.value = emptyForm()
  dialog.value = true
}

function openEdit(row: any) {
  editingId.value = row.id
  form.value = {
    title: row.title,
    author: row.author,
    cover: row.cover || '',
    category_id: row.category?.id ?? row.category_id ?? 1,
    price: row.price,
    stock: row.stock,
    summary: row.summary || '',
    highlight: row.highlight || '',
    status: row.status || 'published',
  }
  dialog.value = true
}

async function save() {
  const res = editingId.value
    ? await request({
        url: `/admin/books/${editingId.value}`,
        method: 'PUT',
        data: form.value,
      })
    : await request({ url: '/admin/books', method: 'POST', data: form.value })
  if (res.code === 200) {
    dialog.value = false
    load()
  } else {
    alert(res.msg)
  }
}

async function remove(id: number) {
  if (!confirm('确定删除？')) return
  await request({ url: `/admin/books/${id}`, method: 'DELETE' })
  load()
}

onMounted(load)
</script>

<template>
  <div class="page-card">
    <div class="page-header">
      <h2>书籍管理</h2>
      <el-button type="primary" @click="openCreate">+ 新增书籍</el-button>
    </div>
    <el-table :data="books">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="title" label="书名" />
      <el-table-column prop="author" label="作者" />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column prop="stock" label="库存" width="80" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="remove(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" :title="editingId ? '编辑书籍' : '新增书籍'" width="500px">
      <el-form label-width="80px">
        <el-form-item label="书名"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="作者"><el-input v-model="form.author" /></el-form-item>
        <el-form-item label="封面">
          <CoverUpload v-model="form.cover" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category_id">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="价格"><el-input-number v-model="form.price" :min="0" /></el-form-item>
        <el-form-item label="库存"><el-input-number v-model="form.stock" :min="0" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status">
            <el-option label="已发布" value="published" />
            <el-option label="草稿" value="draft" />
            <el-option label="已下架" value="off_shelf" />
          </el-select>
        </el-form-item>
        <el-form-item label="简介"><el-input v-model="form.summary" type="textarea" /></el-form-item>
        <el-form-item label="金句"><el-input v-model="form.highlight" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
