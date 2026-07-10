<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadRequestOptions } from 'element-plus'
import { request } from '@/api/client'
import { uploadHomePageVideo, deleteHomePageVideo } from '@/utils/adminUpload'
import { resolveMediaUrl } from '@/utils/media'
import { protectVideoUrl } from '@/utils/video'

const MAX_VIDEOS = 6

const videos = defineModel<string[]>({ default: () => [] })

const uploading = ref(false)
const storageDir = ref('')

const canAddMore = computed(() => videos.value.length < MAX_VIDEOS)

async function loadStorageInfo() {
  try {
    const res = await request<{ storage_dir?: string; urls?: string[] }>({
      url: '/admin/home-page-videos',
    })
    if (res.code === 200 && res.data) {
      storageDir.value = res.data.storage_dir || ''
    }
  } catch {
    // ignore
  }
}

onMounted(loadStorageInfo)

function displayUrl(url: string) {
  return protectVideoUrl(resolveMediaUrl(url))
}

async function handleUpload(options: UploadRequestOptions) {
  if (!canAddMore.value) {
    ElMessage.warning(`最多上传 ${MAX_VIDEOS} 个背景视频`)
    options.onError?.(new Error('limit reached') as never)
    return
  }

  uploading.value = true
  try {
    const data = await uploadHomePageVideo(options.file)
    if (data.media_type !== 'video') {
      ElMessage.warning('首页背景仅支持视频，请上传 MP4/WebM')
      options.onError?.(new Error('not video') as never)
      return
    }
    videos.value = [...videos.value, data.url]
    await loadStorageInfo()
    ElMessage.success(`已添加背景视频（${videos.value.length}/${MAX_VIDEOS}）`)
    options.onSuccess?.(data)
  } catch (err) {
    const message = err instanceof Error ? err.message : '上传失败，请稍后重试'
    ElMessage.error(message === 'upload failed' ? '上传失败，请稍后重试' : message)
    options.onError?.(new Error(message) as never)
  } finally {
    uploading.value = false
  }
}

function beforeUpload(file: File) {
  if (!file.type.startsWith('video/')) {
    ElMessage.warning('仅支持视频 MP4/WebM')
    return false
  }
  if (file.size > 100 * 1024 * 1024) {
    ElMessage.warning('视频大小不能超过 100MB')
    return false
  }
  return true
}

function homePageDeleteUrl(url: string): string | null {
  if (url.startsWith('/uploads/homePage/')) return url
  const name = url.split('/').filter(Boolean).pop()
  if (name && /\.(mp4|webm)$/i.test(name)) {
    return `/uploads/homePage/${name}`
  }
  return null
}

async function removeVideo(index: number) {
  const url = videos.value[index]
  if (!url) return
  try {
    const deleteUrl = homePageDeleteUrl(url)
    if (deleteUrl) {
      await deleteHomePageVideo(deleteUrl)
    }
    videos.value = videos.value.filter((_, i) => i !== index)
    await loadStorageInfo()
    ElMessage.success('已删除背景视频')
  } catch (err) {
    const message = err instanceof Error ? err.message : '删除失败'
    ElMessage.error(message)
  }
}

function moveVideo(index: number, delta: number) {
  const next = [...videos.value]
  const target = index + delta
  if (target < 0 || target >= next.length) return
  ;[next[index], next[target]] = [next[target], next[index]]
  videos.value = next
}
</script>

<template>
  <div class="bg-videos">
    <p class="tip">
      视频与磁盘目录实时同步：上传/删除会立即写入存储目录。保存时不在列表中的文件会被清理。
    </p>
    <p v-if="storageDir" class="storage-dir">存储目录：{{ storageDir }}</p>

    <div v-if="videos.length" class="video-list">
      <div v-for="(url, index) in videos" :key="`${url}-${index}`" class="video-item">
        <div class="video-preview-wrap">
          <video
            :src="displayUrl(url)"
            class="video-preview"
            muted
            playsinline
            preload="metadata"
            disablepictureinpicture
            disableremoteplayback
            controlslist="nodownload noremoteplayback"
            referrerpolicy="no-referrer"
            @contextmenu.prevent
          />
          <div class="video-download-shield" aria-hidden="true" @contextmenu.prevent />
          <span class="video-index">视频 {{ index + 1 }}</span>
        </div>
        <div class="video-actions">
          <span class="video-path">{{ url }}</span>
          <div class="action-btns">
            <el-button size="small" :disabled="index === 0" @click="moveVideo(index, -1)">上移</el-button>
            <el-button
              size="small"
              :disabled="index === videos.length - 1"
              @click="moveVideo(index, 1)"
            >
              下移
            </el-button>
            <el-button size="small" type="danger" link @click="removeVideo(index)">删除</el-button>
          </div>
        </div>
      </div>
    </div>

    <el-upload
      v-if="canAddMore"
      class="bg-uploader"
      :show-file-list="false"
      accept=".mp4,.webm"
      :http-request="handleUpload"
      :before-upload="beforeUpload"
      :disabled="uploading"
    >
      <div class="bg-upload-trigger">
        <span class="icon">+</span>
        <span class="text">
          {{ uploading ? '上传中…' : `添加背景视频（${videos.length}/${MAX_VIDEOS}）` }}
        </span>
        <span class="hint">MP4/WebM，单个不超过 100MB，保存至 homePage 目录</span>
      </div>
    </el-upload>

    <el-empty v-else description="已达 6 个视频上限，删除后可继续添加" :image-size="72" />
  </div>
</template>

<style scoped>
.bg-videos {
  width: 100%;
}

.tip {
  margin: 0 0 8px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
}

.storage-dir {
  margin: 0 0 12px;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  word-break: break-all;
}

.video-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 12px;
}

.video-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-fill-color-blank);
}

.video-preview-wrap {
  position: relative;
  width: 180px;
  flex-shrink: 0;
  border-radius: 6px;
  overflow: hidden;
  background: #000;
}

.video-preview {
  display: block;
  width: 100%;
  max-height: 120px;
  object-fit: cover;
}

.video-index {
  position: absolute;
  top: 6px;
  left: 6px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #fff;
  background: rgba(0, 0, 0, 0.55);
}

.video-actions {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 8px;
}

.video-path {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  word-break: break-all;
}

.action-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.bg-uploader :deep(.el-upload) {
  width: 100%;
}

.bg-upload-trigger {
  width: 100%;
  min-height: 96px;
  border: 1px dashed var(--el-border-color);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 16px;
  cursor: pointer;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color-light);
  transition: border-color 0.2s;
}

.bg-upload-trigger:hover {
  border-color: var(--el-color-primary);
}

.bg-upload-trigger .icon {
  font-size: 24px;
  color: var(--el-color-primary);
}

.bg-upload-trigger .text {
  font-size: 14px;
}

.bg-upload-trigger .hint {
  font-size: 12px;
  opacity: 0.75;
}
</style>
