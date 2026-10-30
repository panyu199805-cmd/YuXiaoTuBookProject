<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadRequestOptions } from 'element-plus'
import { request } from '@/api/client'
import { uploadBookReviewVideo, deleteBookReviewVideo } from '@/utils/adminUpload'
import { resolveMediaUrl } from '@/utils/media'
import { protectVideoUrl } from '@/utils/video'

const MAX_VIDEOS = 20

const videos = defineModel<string[]>({ default: () => [] })

const props = withDefaults(
  defineProps<{
    allowDeleteFile?: boolean
  }>(),
  { allowDeleteFile: false },
)

const uploading = ref(false)
const storageDir = ref('')
const libraryUrls = ref<string[]>([])
const pickerVisible = ref(false)
const urlInput = ref('')

function isExternalUrl(url: string) {
  return /^https?:\/\//i.test(url.trim())
}

function isValidVideoUrl(url: string) {
  const value = url.trim()
  if (!value) return false
  if (isExternalUrl(value)) return true
  return value.startsWith('/uploads/')
}

const canAddMore = computed(() => videos.value.length < MAX_VIDEOS)
const availableLibrary = computed(() =>
  libraryUrls.value.filter((url) => !videos.value.includes(url)),
)

async function loadStorageInfo() {
  try {
    const res = await request<{ storage_dir?: string; urls?: string[] }>({
      url: '/admin/book-review-videos',
    })
    if (res.code === 200 && res.data) {
      storageDir.value = res.data.storage_dir || ''
      libraryUrls.value = res.data.urls || []
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
    ElMessage.warning(`每本书最多添加 ${MAX_VIDEOS} 个解读视频`)
    options.onError?.(new Error('limit reached') as never)
    return
  }

  uploading.value = true
  try {
    const data = await uploadBookReviewVideo(options.file)
    if (data.media_type !== 'video') {
      ElMessage.warning('解读视频仅支持 MP4/WebM')
      options.onError?.(new Error('not video') as never)
      return
    }
    videos.value = [...videos.value, data.url]
    await loadStorageInfo()
    ElMessage.success(`已添加解读视频（${videos.value.length}/${MAX_VIDEOS}）`)
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

function addFromLibrary(url: string) {
  if (!canAddMore.value) {
    ElMessage.warning(`每本书最多添加 ${MAX_VIDEOS} 个解读视频`)
    return
  }
  if (videos.value.includes(url)) return
  videos.value = [...videos.value, url]
  pickerVisible.value = false
  ElMessage.success('已从目录添加视频')
}

function addByUrl() {
  const url = urlInput.value.trim()
  if (!url) {
    ElMessage.warning('请输入视频链接')
    return
  }
  if (!isValidVideoUrl(url)) {
    ElMessage.warning('请输入有效的 http(s) 链接或 /uploads/ 路径')
    return
  }
  if (!canAddMore.value) {
    ElMessage.warning(`每本书最多添加 ${MAX_VIDEOS} 个解读视频`)
    return
  }
  if (videos.value.includes(url)) {
    ElMessage.warning('该视频已在列表中')
    return
  }
  videos.value = [...videos.value, url]
  urlInput.value = ''
  ElMessage.success('已添加视频链接')
}

async function removeVideo(index: number) {
  const url = videos.value[index]
  if (!url) return
  if (props.allowDeleteFile && !isExternalUrl(url)) {
    try {
      await deleteBookReviewVideo(url)
      await loadStorageInfo()
    } catch (err) {
      const message = err instanceof Error ? err.message : '删除文件失败'
      ElMessage.error(message)
      return
    }
  }
  videos.value = videos.value.filter((_, i) => i !== index)
  ElMessage.success(props.allowDeleteFile ? '已删除视频文件' : '已从列表移除')
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
  <div class="review-videos">
    <p class="tip">
      支持上传本地视频、从 bookReview 目录选择，或直接填写 http(s) / /uploads/ 链接。按列表顺序连播。
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
          <span class="video-index">
            第 {{ index + 1 }} 条
            <template v-if="isExternalUrl(url)"> · 外链</template>
          </span>
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
            <el-button size="small" type="danger" link @click="removeVideo(index)">
              {{ allowDeleteFile ? '删除文件' : '移除' }}
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <div class="url-add">
      <el-input
        v-model="urlInput"
        placeholder="粘贴视频链接，如 https://example.com/video.mp4 或 /uploads/bookReview/xxx.mp4"
        clearable
        @keyup.enter="addByUrl"
      />
      <el-button :disabled="!canAddMore" @click="addByUrl">添加链接</el-button>
    </div>

    <div class="toolbar">
      <el-upload
        v-if="canAddMore"
        class="review-uploader"
        :show-file-list="false"
        accept=".mp4,.webm"
        :http-request="handleUpload"
        :before-upload="beforeUpload"
        :disabled="uploading"
      >
        <div class="review-upload-trigger">
          <span class="icon">+</span>
          <span class="text">
            {{ uploading ? '上传中…' : `上传解读视频（${videos.length}/${MAX_VIDEOS}）` }}
          </span>
          <span class="hint">MP4/WebM，单个不超过 100MB</span>
        </div>
      </el-upload>

      <el-button v-if="canAddMore && availableLibrary.length" @click="pickerVisible = true">
        从 bookReview 目录选择
      </el-button>
    </div>

    <el-empty
      v-if="!canAddMore"
      description="已达视频上限，移除后可继续添加"
      :image-size="72"
    />

    <el-dialog v-model="pickerVisible" title="从 bookReview 目录选择" width="520px">
      <div v-if="availableLibrary.length" class="library-list">
        <button
          v-for="url in availableLibrary"
          :key="url"
          type="button"
          class="library-item"
          @click="addFromLibrary(url)"
        >
          {{ url }}
        </button>
      </div>
      <el-empty v-else description="目录中暂无可选视频" :image-size="64" />
    </el-dialog>
  </div>
</template>

<style scoped>
.review-videos {
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

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: stretch;
}

.url-add {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.url-add .el-input {
  flex: 1;
}

.review-uploader {
  flex: 1;
  min-width: 240px;
}

.review-uploader :deep(.el-upload) {
  width: 100%;
}

.review-upload-trigger {
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
}

.review-upload-trigger .icon {
  font-size: 24px;
  color: var(--el-color-primary);
}

.review-upload-trigger .text {
  font-size: 14px;
}

.review-upload-trigger .hint {
  font-size: 12px;
  opacity: 0.75;
}

.library-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 360px;
  overflow: auto;
}

.library-item {
  text-align: left;
  padding: 10px 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-fill-color-blank);
  cursor: pointer;
  font-size: 13px;
  word-break: break-all;
}

.library-item:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}
</style>
