<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { request } from '@/api/client'
import { useSiteStore } from '@/stores/site'
import BackgroundVideosUpload from '@/components/admin/BackgroundVideosUpload.vue'

const siteStore = useSiteStore()

const form = ref({
  bg_type: 'video',
  bg_url: '',
  bg_videos: [] as string[],
  featured_book_id: undefined as number | undefined,
  promo_title: '',
  daily_sentence: '',
})

async function load() {
  const res = await request<any>({ url: '/admin/site-config' })
  if (res.code === 200 && res.data) {
    const data = res.data
    const list = Array.isArray(data.bg_videos)
      ? data.bg_videos
      : data.bg_url
        ? [data.bg_url]
        : []
    form.value = {
      ...form.value,
      ...data,
      bg_videos: list,
      bg_type: list.length ? 'video' : 'image',
    }
  }
}

async function save() {
  const payload = {
    ...form.value,
    bg_type: form.value.bg_videos.length ? 'video' : 'image',
    bg_url: form.value.bg_videos[0] || '',
    bg_videos: form.value.bg_videos.length ? form.value.bg_videos : [],
    bg_enabled: form.value.bg_videos.length > 0,
  }
  const res = await request<any>({ url: '/admin/site-config', method: 'PUT', data: payload })
  if (res.code === 200) {
    if (res.data) {
      form.value.bg_videos = Array.isArray(res.data.bg_videos) ? res.data.bg_videos : []
      form.value.bg_url = res.data.bg_url || ''
      form.value.bg_type = res.data.bg_type || 'image'
    }
    await siteStore.fetchConfig(true)
    const purged = Number(res.data?.purged_videos?.length || 0)
    alert(purged > 0 ? `保存成功，已清理 ${purged} 个 homePage 视频文件` : '保存成功')
  } else {
    alert(res.msg || '保存失败')
  }
}

onMounted(load)
</script>

<template>
  <div class="page-card">
    <div class="page-header">
      <h2>氛围配置</h2>
    </div>
    <el-form label-width="120px" style="max-width: 720px">
      <el-form-item label="首页背景">
        <BackgroundVideosUpload v-model="form.bg_videos" />
      </el-form-item>
      <el-form-item label="宣传标题"><el-input v-model="form.promo_title" placeholder="读书视频，宇小兔更懂你" /></el-form-item>
      <el-form-item label="今日金句"><el-input v-model="form.daily_sentence" /></el-form-item>
      <el-form-item label="主推书籍ID">
        <el-input-number v-model="form.featured_book_id" :min="1" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="save">保存</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>
