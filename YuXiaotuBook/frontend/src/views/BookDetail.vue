<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useHead } from '@unhead/vue'
import VideoPlayer from '@/components/VideoPlayer.vue'
import BookCard from '@/components/BookCard.vue'
import EbookReader from '@/components/EbookReader.vue'
import { request } from '@/api/client'
import { useUserStore } from '@/stores/user'
import { inlineCoverFallback, placeholderCover, resolveMediaUrl } from '@/utils/media'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const book = ref<any>(null)
const videoUrl = ref('')
const videoPoster = ref('')
const maxDuration = ref<number | null>(null)
const fullAccess = ref(true)
const similar = ref<any[]>([])
const bookCover = ref('')
const showOrder = ref(false)
const submitting = ref(false)
const orderForm = ref({
  quantity: 1,
  receiver_name: '',
  receiver_phone: '',
  receiver_address: '',
})

function onBookCoverError() {
  if (!book.value) return
  const fallback = placeholderCover(book.value.id)
  bookCover.value =
    bookCover.value === fallback ? inlineCoverFallback(book.value.title, book.value.id) : fallback
}

async function load() {
  const id = route.params.id
  book.value = null
  similar.value = []
  videoUrl.value = ''
  videoPoster.value = ''
  bookCover.value = ''
  showOrder.value = false

  const res = await request<any>({ url: `/books/${id}` })
  if (res.code === 200) {
    book.value = res.data
    bookCover.value = resolveMediaUrl(res.data.cover, res.data.id)
    useHead({ title: `${res.data.title} - 宇小兔每日读书` })
    if (res.data.has_video) {
      const play = await request<any>({ url: `/books/${id}/play-auth` })
      if (play.code === 200) {
        videoUrl.value = play.data.video_url
        videoPoster.value = play.data.poster
        fullAccess.value = play.data.full_access
        maxDuration.value = play.data.max_duration ?? null
      }
    }
  } else {
    book.value = null
    alert(res.msg || '书籍不存在')
    return
  }

  const sim = await request<any[]>({ url: `/books/${id}/similar` })
  if (sim.code === 200) similar.value = sim.data || []
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function toggleFavorite() {
  if (!store.isLoggedIn) {
    router.push({ name: 'Login', query: { redirect: route.fullPath } })
    return
  }
  await request({ url: '/favorites', method: 'POST', data: { book_id: book.value.id } })
  alert('收藏成功')
}

function validateOrderForm() {
  const { receiver_name, receiver_phone, receiver_address } = orderForm.value
  if (!receiver_name.trim()) {
    alert('请填写收货人')
    return false
  }
  if (!/^1\d{10}$/.test(receiver_phone.trim())) {
    alert('请填写正确的 11 位手机号')
    return false
  }
  if (!receiver_address.trim()) {
    alert('请填写收货地址')
    return false
  }
  return true
}

async function submitOrder() {
  if (!store.isLoggedIn) {
    router.push({ name: 'Login', query: { redirect: route.fullPath } })
    return
  }
  if (!validateOrderForm() || submitting.value) return

  submitting.value = true
  try {
    const res = await request<{ id: number }>({
      url: '/orders',
      method: 'POST',
      data: {
        book_id: book.value.id,
        quantity: orderForm.value.quantity,
        receiver_name: orderForm.value.receiver_name.trim(),
        receiver_phone: orderForm.value.receiver_phone.trim(),
        receiver_address: orderForm.value.receiver_address.trim(),
      },
    })
    if (res.code === 401) {
      alert('登录已失效，请重新登录')
      store.logout()
      router.push({ name: 'Login', query: { redirect: route.fullPath } })
      return
    }
    if (res.code !== 200 || !res.data?.id) {
      alert(res.msg || '下单失败')
      return
    }

    const pay = await request({
      url: `/orders/${res.data.id}/mock-pay`,
      method: 'POST',
    })
    if (pay.code === 200) {
      alert('下单并模拟支付成功')
      showOrder.value = false
      router.push('/user/orders')
    } else {
      alert(pay.msg || '支付失败，请前往订单页重试')
      router.push('/user/orders')
    }
  } catch (e) {
    console.error(e)
    alert('网络异常：请确认 Java 交易服务已启动（端口 8081）')
  } finally {
    submitting.value = false
  }
}

function onPreviewEnded() {
  if (!store.isLoggedIn) {
    router.push({ name: 'Login', query: { redirect: route.fullPath } })
  }
}

onMounted(load)

watch(
  () => route.params.id,
  (id, prev) => {
    if (id && id !== prev) load()
  }
)
</script>

<template>
  <div class="container page" v-if="book" :key="String(route.params.id)">
    <div v-if="videoUrl" class="video-section">
      <VideoPlayer
        :src="videoUrl"
        :poster="videoPoster"
        :max-duration="fullAccess ? null : maxDuration"
        @preview-ended="onPreviewEnded"
      />
      <p v-if="!fullAccess && maxDuration" class="preview-hint">
        游客试看 {{ Math.floor((maxDuration || 0) / 60) }} 分钟，登录看全片
      </p>
    </div>
    <div v-else-if="book.has_video === false" class="no-video">
      <img :src="bookCover" :alt="book.title" @error="onBookCoverError" />
      <p>解读视频筹备中</p>
    </div>

    <div class="detail">
      <h1>{{ book.title }}</h1>
      <p class="meta">{{ book.author }} · {{ book.category?.name }}</p>
      <p v-if="book.highlight" class="highlight">「{{ book.highlight }}」</p>
      <p class="summary">{{ book.summary }}</p>

      <EbookReader
        v-if="book.ebook_content"
        :title="book.ebook_title || `${book.title} · 电子书解读`"
        :summary="book.highlight"
        :content="book.ebook_content"
      />

      <p v-if="book.target_audience" class="audience">适合：{{ book.target_audience }}</p>
      <p class="price">¥{{ book.price?.toFixed(2) }} · 库存 {{ book.stock }}</p>

      <div class="actions">
        <button class="btn btn-outline" @click="toggleFavorite">收藏</button>
        <button
          class="btn btn-primary"
          :disabled="book.stock <= 0"
          @click="showOrder = true"
        >
          {{ book.stock > 0 ? '购买纸质书' : '已售罄' }}
        </button>
      </div>
    </div>

    <div v-if="showOrder" class="order-modal">
      <div class="order-box">
        <h3>填写收货信息</h3>
        <input v-model="orderForm.receiver_name" placeholder="收货人" />
        <input v-model="orderForm.receiver_phone" placeholder="手机号" />
        <textarea v-model="orderForm.receiver_address" placeholder="收货地址" rows="3" />
        <div class="order-actions">
          <button class="btn btn-outline" @click="showOrder = false">取消</button>
          <button class="btn btn-primary" :disabled="submitting" @click="submitOrder">
            {{ submitting ? '提交中…' : '确认下单' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="similar.length" class="similar">
      <h2>相似推荐</h2>
      <div class="grid">
        <BookCard v-for="b in similar" :key="b.id" :id="b.id" v-bind="b" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { padding-top: 32px; }
.video-section { margin-bottom: 32px; }
.no-video { text-align: center; padding: 40px; }
.no-video img { max-width: 200px; border-radius: 8px; }
.preview-hint {
  margin-top: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
  text-align: center;
}
.detail h1 { font-size: 28px; margin-bottom: 8px; }
.meta { color: var(--color-text-secondary); }
.highlight { color: var(--color-accent); margin: 16px 0; font-size: 18px; }
.summary { margin: 16px 0; }
.price { font-size: 20px; color: var(--color-primary); font-weight: 600; margin: 16px 0; }
.actions { display: flex; gap: 12px; margin-top: 20px; }
.similar { margin-top: 48px; }
.similar h2 { margin-bottom: 20px; }
.grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.order-modal {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center; z-index: 200;
}
.order-box {
  background: #fff; padding: 24px; border-radius: 8px; width: 400px; max-width: 90%;
  display: flex; flex-direction: column; gap: 12px;
}
.order-box input, .order-box textarea {
  padding: 10px; border: 1px solid var(--color-border); border-radius: 6px;
}
.order-actions { display: flex; gap: 12px; justify-content: flex-end; }
@media (max-width: 1023px) { .grid { grid-template-columns: repeat(2, 1fr); } }
</style>
