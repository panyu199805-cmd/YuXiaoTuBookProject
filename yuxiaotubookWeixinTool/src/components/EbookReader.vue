<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const props = defineProps<{
  title: string
  /** 收起态展示的简介，对应详情页 summary 位置 */
  teaser?: string
  ebookContent: string
}>()

const expanded = ref(false)
const isFullscreen = ref(false)
const fontIndex = ref(1)
const themeIndex = ref(0)
const tocOpen = ref(false)
const scrollIntoView = ref('')

const FONT_SIZES = [26, 30, 34] as const
const FONT_LABELS = ['小字', '标准', '大字'] as const

const THEMES = [
  {
    name: '米色',
    page: '#fdfbf7',
    header: '#faf6ef',
    footer: '#faf6ef',
    text: '#2a2a2a',
    heading: '#3d3d3d',
    step: '#5b4a2a',
    border: 'rgba(201, 169, 98, 0.22)',
    stepBorder: '#c9a962',
  },
  {
    name: '纯白',
    page: '#ffffff',
    header: '#f5f5f5',
    footer: '#f5f5f5',
    text: '#1a1a1a',
    heading: '#2d2d2d',
    step: '#4a4a4a',
    border: 'rgba(0, 0, 0, 0.08)',
    stepBorder: '#5b9aa0',
  },
  {
    name: '护眼绿',
    page: '#e8f3e6',
    header: '#dcefdc',
    footer: '#dcefdc',
    text: '#1e3a24',
    heading: '#2d4a32',
    step: '#3d5c42',
    border: 'rgba(76, 140, 90, 0.25)',
    stepBorder: '#4c8c5a',
  },
  {
    name: '深色',
    page: '#2a2826',
    header: '#1f1e1c',
    footer: '#1f1e1c',
    text: '#e8e4dc',
    heading: '#f0ebe3',
    step: '#d4c4a8',
    border: 'rgba(255, 255, 255, 0.1)',
    stepBorder: '#c9a962',
  },
] as const

const currentTheme = computed(() => THEMES[themeIndex.value])
const currentFontSize = computed(() => FONT_SIZES[fontIndex.value])

const paragraphs = computed(() =>
  (props.ebookContent || '')
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

function exitFullscreen() {
  isFullscreen.value = false
}

function toggleFullscreen() {
  if (!expanded.value) expanded.value = true
  isFullscreen.value = !isFullscreen.value
  if (isFullscreen.value) tocOpen.value = false
}

function cycleFont() {
  fontIndex.value = (fontIndex.value + 1) % FONT_SIZES.length
  uni.showToast({ title: FONT_LABELS[fontIndex.value], icon: 'none', duration: 800 })
}

function cycleTheme() {
  themeIndex.value = (themeIndex.value + 1) % THEMES.length
  uni.showToast({ title: currentTheme.value.name, icon: 'none', duration: 800 })
}

function toggleToc() {
  tocOpen.value = !tocOpen.value
}

function scrollToChapter(index: number) {
  scrollIntoView.value = ''
  setTimeout(() => {
    scrollIntoView.value = `para-${index}`
  }, 30)
  tocOpen.value = false
}

function collapse() {
  expanded.value = false
  exitFullscreen()
  tocOpen.value = false
}

watch(expanded, (open) => {
  if (!open) {
    exitFullscreen()
    tocOpen.value = false
  }
})
</script>

<template>
  <view class="ebook-reader" :class="{ expanded, 'is-fullscreen': isFullscreen }">
    <view v-if="!expanded" class="ebook-entry" @tap="toggle">
      <text class="ebook-entry-text">{{ teaser || '点击展开，阅读完整电子书' }}</text>
      <text class="ebook-entry-action">展开阅读 ↓</text>
    </view>

    <view v-else class="ebook-panel">
      <view
        class="ebook-page"
        :class="{ 'ebook-page--fullscreen': isFullscreen }"
        :style="{
          background: currentTheme.page,
          borderColor: currentTheme.border,
        }"
      >
        <view
          class="ebook-header"
          :style="{ background: currentTheme.header, borderColor: currentTheme.border }"
        >
          <view class="ebook-header-left">
            <view class="ebook-toc-wrap">
              <view
                class="ebook-tool"
                :class="{ active: tocOpen }"
                @tap.stop="toggleToc"
              >
                <text class="tool-icon">☰</text>
              </view>
              <view v-if="tocOpen" class="ebook-toc-panel" @tap.stop>
                <text class="ebook-toc-head">章节目录</text>
                <scroll-view v-if="chapters.length" scroll-y class="ebook-toc-list">
                  <view
                    v-for="chapter in chapters"
                    :key="chapter.index"
                    class="ebook-toc-item"
                    :class="`level-${chapter.level}`"
                    @tap="scrollToChapter(chapter.index)"
                  >
                    <text>{{ chapter.title }}</text>
                  </view>
                </scroll-view>
                <text v-else class="ebook-toc-empty">暂无章节目录</text>
              </view>
            </view>
            <text class="ebook-title" :style="{ color: currentTheme.heading }">{{ title }}</text>
          </view>
          <view class="ebook-toolbar">
            <view class="ebook-tool" @tap.stop="toggleFullscreen">
              <text class="tool-icon">{{ isFullscreen ? '⊡' : '⛶' }}</text>
            </view>
            <view class="ebook-tool ebook-tool--font" @tap.stop="cycleFont">
              <text class="font-icon">A</text>
              <text class="font-icon font-icon--sm">a</text>
            </view>
            <view class="ebook-tool" @tap.stop="cycleTheme">
              <view
                class="theme-dot"
                :style="{ background: currentTheme.page, borderColor: currentTheme.border }"
              />
            </view>
            <view class="ebook-close" @tap.stop="collapse">
              <text>收起</text>
            </view>
          </view>
        </view>

        <scroll-view
          scroll-y
          class="ebook-body"
          :scroll-into-view="scrollIntoView"
          scroll-with-animation
          :style="{
            background: currentTheme.page,
            color: currentTheme.text,
            fontSize: currentFontSize + 'rpx',
          }"
        >
          <view
            v-for="item in displayParagraphs"
            :id="`para-${item.index}`"
            :key="item.index"
            class="ebook-para"
            :class="{
              'is-heading': isSectionHeading(item.text),
              'is-step': isStepHeading(item.text),
            }"
            :style="{
              color: isStepHeading(item.text)
                ? currentTheme.step
                : isSectionHeading(item.text)
                  ? currentTheme.heading
                  : currentTheme.text,
              borderLeftColor: isStepHeading(item.text) ? currentTheme.stepBorder : 'transparent',
              fontSize: isStepHeading(item.text) ? currentFontSize + 2 + 'rpx' : undefined,
            }"
          >
            <text>{{ item.text }}</text>
          </view>
          <view v-if="!isFullscreen" class="ebook-body-spacer" />
        </scroll-view>

        <view
          v-if="!isFullscreen"
          class="ebook-footer"
          :style="{ background: currentTheme.footer, borderColor: currentTheme.border }"
        >
          <text class="ebook-footer-text">— 全文完 —</text>
          <view class="ebook-close-bottom" @tap="collapse">
            <text>收起阅读</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="tocOpen && !isFullscreen" class="ebook-toc-mask" @tap="tocOpen = false" />
    <view v-if="isFullscreen" class="ebook-fullscreen-mask" />
  </view>
</template>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.ebook-reader {
  margin: 20rpx 0 24rpx;
  position: relative;
}

.ebook-entry {
  padding: 4rpx 0 8rpx;
}

.ebook-entry-text {
  display: block;
  color: $color-text-secondary;
  font-size: 28rpx;
  line-height: 1.7;
}

.ebook-entry-action {
  display: block;
  margin-top: 12rpx;
  font-size: 26rpx;
  font-weight: 600;
  color: $color-primary;
}

.ebook-collapsed {
  display: flex;
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.06);
}

.book-spine {
  width: 20rpx;
  flex-shrink: 0;
  background: linear-gradient(180deg, #4a858b 0%, #5b9aa0 50%, #3d7177 100%);
}

.book-face {
  flex: 1;
  padding: 32rpx 36rpx;
  background: linear-gradient(135deg, #fdfbf7 0%, #f5f0e8 100%);
  border: 1rpx solid rgba(201, 169, 98, 0.25);
  border-left: none;
}

.book-badge {
  display: inline-block;
  font-size: 22rpx;
  font-weight: 600;
  color: #8b6914;
  background: rgba(201, 169, 98, 0.18);
  padding: 6rpx 18rpx;
  border-radius: 999rpx;
  margin-bottom: 16rpx;
}

.book-teaser {
  display: block;
  font-size: 30rpx;
  color: $color-text;
  line-height: 1.6;
  margin-bottom: 12rpx;
}

.book-hint {
  display: block;
  font-size: 24rpx;
  color: $color-text-secondary;
  margin-bottom: 16rpx;
}

.book-action {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
  color: $color-primary;
}

.ebook-panel {
  margin-top: 24rpx;
}

.ebook-reader.is-fullscreen .ebook-panel {
  position: fixed;
  inset: 0;
  z-index: 9999;
  margin: 0;
  padding: 0;
}

.ebook-fullscreen-mask {
  display: none;
}

.ebook-page {
  border: 1rpx solid rgba(201, 169, 98, 0.22);
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: 0 12rpx 40rpx rgba(0, 0, 0, 0.06);
}

.ebook-page--fullscreen {
  border-radius: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  border: none;
  box-shadow: none;
}

.ebook-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
  padding: 28rpx 28rpx 24rpx;
  border-bottom: 1rpx solid rgba(201, 169, 98, 0.2);
  flex-wrap: wrap;
}

.ebook-header-left {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
  flex: 1;
  min-width: 0;
}

.ebook-toc-wrap {
  position: relative;
  flex-shrink: 0;
}

.ebook-tool {
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1rpx solid $color-border;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 999rpx;
}

.ebook-tool.active {
  color: $color-primary;
  border-color: rgba(91, 154, 160, 0.45);
}

.tool-icon {
  font-size: 28rpx;
  line-height: 1;
  color: $color-text-secondary;
}

.ebook-tool--font {
  gap: 2rpx;
}

.font-icon {
  font-size: 24rpx;
  font-weight: 700;
  line-height: 1;
  color: $color-text-secondary;
}

.font-icon--sm {
  font-size: 18rpx;
  font-weight: 600;
}

.theme-dot {
  width: 24rpx;
  height: 24rpx;
  border-radius: 50%;
  border: 2rpx solid;
}

.ebook-title {
  flex: 1;
  font-size: 32rpx;
  font-weight: 700;
  line-height: 1.5;
}

.ebook-toolbar {
  display: flex;
  align-items: center;
  gap: 10rpx;
  flex-shrink: 0;
}

.ebook-close {
  padding: 10rpx 24rpx;
  border: 1rpx solid $color-border;
  background: #fff;
  border-radius: 999rpx;
}

.ebook-close text {
  font-size: 24rpx;
  color: $color-text-secondary;
}

.ebook-toc-mask {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: transparent;
}

.ebook-toc-panel {
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 200;
  width: 520rpx;
  max-height: 520rpx;
  margin-top: 8rpx;
  border: 1rpx solid rgba(201, 169, 98, 0.28);
  border-radius: 20rpx;
  background: #fdfbf7;
  box-shadow: 0 16rpx 48rpx rgba(0, 0, 0, 0.12);
  overflow: hidden;
}

.ebook-toc-head {
  display: block;
  padding: 20rpx 24rpx 12rpx;
  font-size: 24rpx;
  font-weight: 700;
  color: #3d3d3d;
  border-bottom: 1rpx solid rgba(201, 169, 98, 0.18);
}

.ebook-toc-list {
  max-height: 440rpx;
  padding: 12rpx;
}

.ebook-toc-item {
  padding: 16rpx 18rpx;
  border-radius: 12rpx;
}

.ebook-toc-item text {
  font-size: 24rpx;
  line-height: 1.5;
  color: #2a2a2a;
}

.ebook-toc-item.level-2 {
  padding-left: 36rpx;
}

.ebook-toc-item.level-2 text {
  font-size: 22rpx;
}

.ebook-toc-empty {
  display: block;
  padding: 24rpx;
  font-size: 24rpx;
  color: $color-text-secondary;
}

.ebook-body {
  max-height: 68vh;
  padding: 36rpx 40rpx;
  box-sizing: border-box;
}

.ebook-page--fullscreen .ebook-body {
  flex: 1;
  max-height: none;
  height: 0;
}

.ebook-para {
  display: block;
  margin-bottom: 1.1em;
  text-indent: 2em;
  line-height: 1.9;
  letter-spacing: 0.02em;
  text-align: justify;
}

.ebook-para.is-heading {
  text-indent: 0;
  font-weight: 600;
  margin-top: 1.2em;
}

.ebook-para.is-step {
  text-indent: 0;
  padding-left: 20rpx;
  border-left: 4rpx solid #c9a962;
}

.ebook-body-spacer {
  height: 40rpx;
}

.ebook-footer {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20rpx;
  padding: 28rpx 36rpx 32rpx;
  border-top: 1rpx solid rgba(201, 169, 98, 0.18);
}

.ebook-footer-text {
  font-size: 24rpx;
  color: $color-text-secondary;
}

.ebook-close-bottom {
  background: $color-primary;
  padding: 16rpx 40rpx;
  border-radius: 999rpx;
}

.ebook-close-bottom text {
  color: #fff;
  font-size: 28rpx;
}
</style>
