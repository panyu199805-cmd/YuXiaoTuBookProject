<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps<{
  title: string
  summary?: string
  content: string
}>()

const expanded = ref(false)
const pageRef = ref<HTMLElement | null>(null)
const bodyRef = ref<HTMLElement | null>(null)
const isFullscreen = ref(false)
const fontIndex = ref(1)
const themeIndex = ref(0)
const tocOpen = ref(false)

const FONT_SIZES = [15, 17, 19] as const
const FONT_LABELS = ['小字', '标准', '大字'] as const

const THEMES = [
  {
    name: '米色',
    page: '#fdfbf7',
    header: 'linear-gradient(180deg, #faf6ef 0%, #fdfbf7 100%)',
    footer: '#faf6ef',
    text: '#2a2a2a',
    heading: '#3d3d3d',
    step: '#5b4a2a',
    border: 'rgba(201, 169, 98, 0.22)',
  },
  {
    name: '纯白',
    page: '#ffffff',
    header: 'linear-gradient(180deg, #f5f5f5 0%, #ffffff 100%)',
    footer: '#f5f5f5',
    text: '#1a1a1a',
    heading: '#2d2d2d',
    step: '#4a4a4a',
    border: 'rgba(0, 0, 0, 0.08)',
  },
  {
    name: '护眼绿',
    page: '#e8f3e6',
    header: 'linear-gradient(180deg, #dcefdc 0%, #e8f3e6 100%)',
    footer: '#dcefdc',
    text: '#1e3a24',
    heading: '#2d4a32',
    step: '#3d5c42',
    border: 'rgba(76, 140, 90, 0.25)',
  },
  {
    name: '深色',
    page: '#2a2826',
    header: 'linear-gradient(180deg, #1f1e1c 0%, #2a2826 100%)',
    footer: '#1f1e1c',
    text: '#e8e4dc',
    heading: '#f0ebe3',
    step: '#d4c4a8',
    border: 'rgba(255, 255, 255, 0.1)',
  },
] as const

const currentTheme = computed(() => THEMES[themeIndex.value])

const pageStyle = computed(() => ({
  '--ebook-bg': currentTheme.value.page,
  '--ebook-header-bg': currentTheme.value.header,
  '--ebook-footer-bg': currentTheme.value.footer,
  '--ebook-text': currentTheme.value.text,
  '--ebook-heading': currentTheme.value.heading,
  '--ebook-step': currentTheme.value.step,
  '--ebook-border': currentTheme.value.border,
  '--ebook-font-size': `${FONT_SIZES[fontIndex.value]}px`,
}))

const paragraphs = computed(() =>
  props.content
    .split(/\n+/)
    .map((p) => p.trim())
    .filter(Boolean),
)

interface ChapterItem {
  index: number
  title: string
  level: number
}

const chapters = computed<ChapterItem[]>(() => {
  const items: ChapterItem[] = []
  paragraphs.value.forEach((text, index) => {
    if (text === '---') return
    if (index === 0) {
      items.push({ index, title: '开篇导读', level: 1 })
      return
    }
    if (isStepHeading(text)) {
      items.push({ index, title: text, level: 2 })
      return
    }
    if (isSectionHeading(text)) {
      items.push({ index, title: text, level: 1 })
    }
  })
  return items
})

const displayParagraphs = computed(() =>
  paragraphs.value
    .map((text, index) => ({ text, index }))
    .filter(({ text }) => text !== '---'),
)

function isStepHeading(text: string) {
  return /^第[一二三四五六七八九十\d]+步：/.test(text)
}

function isSectionHeading(text: string) {
  return (
    isStepHeading(text) ||
    text.startsWith('除了向外表达') ||
    text.startsWith('全书最核心的精髓') ||
    text.startsWith('很多人误以为')
  )
}

function toggle() {
  expanded.value = !expanded.value
  if (!expanded.value) exitFullscreen()
}

function syncFullscreenState() {
  isFullscreen.value = document.fullscreenElement === pageRef.value
}

async function toggleFullscreen() {
  const el = pageRef.value
  if (!el) return
  try {
    if (document.fullscreenElement === el) {
      await document.exitFullscreen()
    } else {
      await el.requestFullscreen()
    }
  } catch {
    isFullscreen.value = !isFullscreen.value
  }
}

function exitFullscreen() {
  if (document.fullscreenElement === pageRef.value) {
    void document.exitFullscreen()
  }
  isFullscreen.value = false
}

function cycleFont() {
  fontIndex.value = (fontIndex.value + 1) % FONT_SIZES.length
}

function cycleTheme() {
  themeIndex.value = (themeIndex.value + 1) % THEMES.length
}

function openToc() {
  tocOpen.value = true
}

function closeToc() {
  tocOpen.value = false
}

function onTocMouseEnter() {
  openToc()
}

function onTocMouseLeave() {
  closeToc()
}

function onTocButtonClick() {
  tocOpen.value = !tocOpen.value
}

function scrollToChapter(index: number) {
  const container = bodyRef.value
  const target = container?.querySelector<HTMLElement>(`[data-para-index="${index}"]`)
  target?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  closeToc()
}

onMounted(() => {
  document.addEventListener('fullscreenchange', syncFullscreenState)
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', syncFullscreenState)
  exitFullscreen()
})

watch(expanded, (open) => {
  if (!open) {
    exitFullscreen()
    closeToc()
  }
})
</script>

<template>
  <div class="ebook-reader" :class="{ expanded, 'is-fullscreen': isFullscreen }">
    <button type="button" class="ebook-collapsed" @click="toggle">
      <div class="book-spine" aria-hidden="true" />
      <div class="book-face">
        <div class="book-badge">电子书解读</div>
        <p v-if="summary" class="book-teaser">{{ summary }}</p>
        <p class="book-hint">{{ expanded ? '点击收起' : '点击展开，阅读完整电子书' }}</p>
        <span class="book-action">
          {{ expanded ? '收起阅读 ↑' : '展开阅读 ↓' }}
        </span>
      </div>
    </button>

    <div v-show="expanded" class="ebook-panel">
      <div
        ref="pageRef"
        class="ebook-page"
        :class="{ 'ebook-page--fullscreen': isFullscreen }"
        :style="pageStyle"
      >
        <header class="ebook-header">
          <div class="ebook-header-left">
            <div
              class="ebook-toc-wrap"
              @mouseenter="onTocMouseEnter"
              @mouseleave="onTocMouseLeave"
            >
              <button
                type="button"
                class="ebook-tool ebook-toc-btn"
                :class="{ active: tocOpen }"
                title="章节目录"
                aria-label="章节目录"
                aria-haspopup="true"
                :aria-expanded="tocOpen"
                @click="onTocButtonClick"
              >
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" stroke-linecap="round" />
                </svg>
              </button>
              <transition name="toc-fade">
                <div v-show="tocOpen" class="ebook-toc-panel">
                  <div class="ebook-toc-head">章节目录</div>
                  <ul v-if="chapters.length" class="ebook-toc-list">
                    <li
                      v-for="chapter in chapters"
                      :key="chapter.index"
                      :class="`level-${chapter.level}`"
                    >
                      <button type="button" @click="scrollToChapter(chapter.index)">
                        {{ chapter.title }}
                      </button>
                    </li>
                  </ul>
                  <p v-else class="ebook-toc-empty">暂无章节目录</p>
                </div>
              </transition>
            </div>
            <h2 class="ebook-title">{{ title }}</h2>
          </div>
          <div class="ebook-toolbar">
            <button
              type="button"
              class="ebook-tool"
              :title="isFullscreen ? '退出全屏' : '全屏阅读'"
              :aria-label="isFullscreen ? '退出全屏' : '全屏阅读'"
              @click="toggleFullscreen"
            >
              <svg v-if="!isFullscreen" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M8 3H3v5M16 3h5v5M16 21h5v-5M8 21H3v-5" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <svg v-else viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 14h6v6M14 20v-6h6M20 10h-6V4M10 4v6H4" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
            <button
              type="button"
              class="ebook-tool ebook-tool--font"
              :title="`切换字体（当前：${FONT_LABELS[fontIndex]}）`"
              aria-label="切换字体大小"
              @click="cycleFont"
            >
              <span class="font-icon">A</span><span class="font-icon font-icon--sm">a</span>
            </button>
            <button
              type="button"
              class="ebook-tool"
              :title="`切换背景（当前：${currentTheme.name}）`"
              aria-label="切换背景颜色"
              @click="cycleTheme"
            >
              <span class="theme-dot" :style="{ background: currentTheme.page, borderColor: currentTheme.border }" />
            </button>
            <button type="button" class="ebook-close" @click="expanded = false">收起</button>
          </div>
        </header>
        <article ref="bodyRef" class="ebook-body">
          <p
            v-for="item in displayParagraphs"
            :key="item.index"
            :data-para-index="item.index"
            :class="{
              'is-heading': isSectionHeading(item.text),
              'is-step': isStepHeading(item.text),
            }"
          >
            {{ item.text }}
          </p>
        </article>
        <footer v-if="!isFullscreen" class="ebook-footer">
          <span>— 全文完 —</span>
          <button type="button" class="ebook-close-bottom" @click="expanded = false">收起阅读</button>
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ebook-reader {
  margin: 16px 0 20px;
}

.ebook-collapsed {
  width: 100%;
  display: flex;
  border: none;
  padding: 0;
  cursor: pointer;
  text-align: left;
  background: transparent;
  font-family: inherit;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--shadow-card);
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.ebook-collapsed:hover {
  box-shadow: 0 6px 24px rgba(91, 154, 160, 0.18);
  transform: translateY(-1px);
}

.book-spine {
  width: 14px;
  flex-shrink: 0;
  background: linear-gradient(180deg, #4a858b 0%, #5b9aa0 50%, #3d7177 100%);
}

.book-face {
  flex: 1;
  padding: 18px 20px;
  background: linear-gradient(135deg, #fdfbf7 0%, #f5f0e8 100%);
  border: 1px solid rgba(201, 169, 98, 0.25);
  border-left: none;
}

.book-badge {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  color: #8b6914;
  background: rgba(201, 169, 98, 0.18);
  padding: 3px 10px;
  border-radius: 999px;
  margin-bottom: 10px;
}

.book-teaser {
  font-size: 16px;
  color: var(--color-text);
  line-height: 1.6;
  margin: 0 0 8px;
}

.book-hint {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0 0 12px;
}

.book-action {
  display: inline-flex;
  align-items: center;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-primary);
}

.ebook-panel {
  margin-top: 14px;
  animation: slideDown 0.28s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.ebook-reader.is-fullscreen .ebook-panel {
  position: fixed;
  inset: 0;
  z-index: 9999;
  margin: 0;
  padding: 0;
  background: rgba(0, 0, 0, 0.5);
}

.ebook-reader.is-fullscreen .ebook-page {
  height: 100%;
  border-radius: 0;
  display: flex;
  flex-direction: column;
}

.ebook-reader.is-fullscreen .ebook-body {
  flex: 1;
  max-height: none;
}

.ebook-page {
  background: var(--ebook-bg, #fdfbf7);
  border: 1px solid var(--ebook-border, rgba(201, 169, 98, 0.22));
  border-radius: 12px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.06),
    inset 0 0 0 1px rgba(255, 255, 255, 0.6);
  overflow: hidden;
  transition: background 0.25s ease, border-color 0.25s ease;
}

.ebook-page:fullscreen,
.ebook-page--fullscreen {
  border-radius: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.ebook-page:fullscreen .ebook-body,
.ebook-page--fullscreen .ebook-body {
  flex: 1;
  max-height: none;
}

.ebook-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 20px 14px;
  border-bottom: 1px solid var(--ebook-border, rgba(201, 169, 98, 0.2));
  background: var(--ebook-header-bg, linear-gradient(180deg, #faf6ef 0%, #fdfbf7 100%));
  transition: background 0.25s ease;
}

.ebook-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 20px 14px;
  border-bottom: 1px solid var(--ebook-border, rgba(201, 169, 98, 0.2));
  background: var(--ebook-header-bg, linear-gradient(180deg, #faf6ef 0%, #fdfbf7 100%));
  transition: background 0.25s ease;
}

.ebook-header-left {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.ebook-toc-wrap {
  position: relative;
  flex-shrink: 0;
}

.ebook-toc-btn.active {
  color: var(--color-primary);
  border-color: rgba(91, 154, 160, 0.45);
  background: #fff;
}

.ebook-toc-panel {
  position: absolute;
  top: calc(100% - 6px);
  left: 0;
  z-index: 20;
  width: min(320px, 72vw);
  max-height: min(360px, 52vh);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding-top: 10px;
  border: 1px solid var(--ebook-border, rgba(201, 169, 98, 0.28));
  border-radius: 12px;
  background: var(--ebook-bg, #fdfbf7);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
}

.ebook-toc-head {
  padding: 12px 14px 8px;
  font-size: 13px;
  font-weight: 700;
  color: var(--ebook-heading, #3d3d3d);
  border-bottom: 1px solid var(--ebook-border, rgba(201, 169, 98, 0.18));
}

.ebook-toc-list {
  list-style: none;
  margin: 0;
  padding: 8px;
  overflow-y: auto;
}

.ebook-toc-list li button {
  width: 100%;
  border: none;
  background: transparent;
  text-align: left;
  padding: 8px 10px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--ebook-text, #2a2a2a);
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s ease, color 0.15s ease;
}

.ebook-toc-list li button:hover {
  background: rgba(91, 154, 160, 0.1);
  color: var(--color-primary);
}

.ebook-toc-list li.level-2 button {
  padding-left: 22px;
  font-size: 12px;
}

.ebook-toc-empty {
  margin: 0;
  padding: 16px 14px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.toc-fade-enter-active,
.toc-fade-leave-active {
  transition: opacity 0.16s ease, transform 0.16s ease;
}

.toc-fade-enter-from,
.toc-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.ebook-title {
  flex: 1;
  min-width: 0;
  font-size: 20px;
  font-weight: 700;
  line-height: 1.5;
  color: var(--ebook-heading, #2c2416);
  margin: 0;
  transition: color 0.25s ease;
}

.ebook-toolbar {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.ebook-tool {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border);
  background: rgba(255, 255, 255, 0.85);
  color: var(--color-text-secondary);
  border-radius: 999px;
  cursor: pointer;
  font-family: inherit;
  padding: 0;
  transition:
    background 0.18s ease,
    color 0.18s ease,
    border-color 0.18s ease,
    transform 0.15s ease;
}

.ebook-tool:hover {
  color: var(--color-primary);
  border-color: rgba(91, 154, 160, 0.45);
  background: #fff;
  transform: translateY(-1px);
}

.ebook-tool--font {
  gap: 1px;
}

.font-icon {
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
}

.font-icon--sm {
  font-size: 10px;
  font-weight: 600;
  margin-top: 2px;
}

.theme-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid;
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.06);
}

.ebook-close {
  flex-shrink: 0;
  border: 1px solid var(--color-border);
  background: #fff;
  color: var(--color-text-secondary);
  font-size: 13px;
  padding: 6px 14px;
  border-radius: 999px;
  cursor: pointer;
  font-family: inherit;
  margin-left: 2px;
}

.ebook-close:hover {
  color: var(--color-primary);
  border-color: rgba(91, 154, 160, 0.4);
}

.ebook-body {
  max-height: min(68vh, 720px);
  overflow-y: auto;
  padding: 24px 28px 32px;
  font-size: var(--ebook-font-size, 16px);
  line-height: 1.9;
  color: var(--ebook-text, #2a2a2a);
  text-align: justify;
  letter-spacing: 0.02em;
  background: var(--ebook-bg, #fdfbf7);
  transition:
    background 0.25s ease,
    color 0.25s ease,
    font-size 0.2s ease;
}

.ebook-body p {
  margin: 0 0 1.1em;
  text-indent: 2em;
}

.ebook-body p.is-heading {
  text-indent: 0;
  font-weight: 600;
  color: var(--ebook-heading, #3d3d3d);
  margin-top: 1.4em;
}

.ebook-body p.is-step {
  color: var(--ebook-step, #5b4a2a);
  font-size: calc(var(--ebook-font-size, 16px) + 1px);
  padding-left: 12px;
  border-left: 3px solid var(--color-accent);
}

.ebook-body::-webkit-scrollbar {
  width: 6px;
}

.ebook-body::-webkit-scrollbar-thumb {
  background: rgba(201, 169, 98, 0.35);
  border-radius: 999px;
}

.ebook-footer {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 16px 24px 20px;
  border-top: 1px solid var(--ebook-border, rgba(201, 169, 98, 0.18));
  background: var(--ebook-footer-bg, #faf6ef);
  color: var(--color-text-secondary);
  font-size: 13px;
  transition: background 0.25s ease;
}

.ebook-close-bottom {
  border: none;
  background: var(--color-primary);
  color: #fff;
  font-size: 14px;
  padding: 8px 20px;
  border-radius: 999px;
  cursor: pointer;
  font-family: inherit;
}

.ebook-close-bottom:hover {
  opacity: 0.92;
}

@media (max-width: 640px) {
  .ebook-header {
    flex-wrap: wrap;
    padding: 14px 14px 12px;
  }

  .ebook-header-left {
    width: 100%;
  }

  .ebook-toolbar {
    width: 100%;
    justify-content: flex-end;
  }

  .ebook-title {
    font-size: 17px;
  }

  .ebook-toc-panel {
    width: min(300px, calc(100vw - 36px));
  }

  .ebook-body {
    padding: 20px 18px 28px;
  }

  .ebook-tool {
    width: 30px;
    height: 30px;
  }
}
</style>
