<script setup lang="ts">
import { ref, watch } from 'vue'
import { placeholderCover, resolveMediaUrl } from '@/utils/media'
import SecureImage from '@/components/SecureImage.vue'
import type { BookListItem } from '@/types/book'

const props = defineProps<{
  book: BookListItem
}>()

const displayCover = ref(resolveMediaUrl(props.book.cover, props.book.id))

watch(
  () => [props.book.cover, props.book.id] as const,
  ([cover, id]) => {
    displayCover.value = resolveMediaUrl(cover, id)
  },
)

function onCoverError() {
  displayCover.value = placeholderCover(props.book.id)
}
</script>

<template>
  <view class="book-card">
    <view class="cover-wrap">
      <SecureImage
        class="cover"
        :src="displayCover"
        mode="aspectFill"
        @error="onCoverError"
      />
      <text v-if="book.has_video === false" class="badge">筹备中</text>
    </view>
    <view class="info">
      <text class="title">{{ book.title }}</text>
      <text class="meta">{{ book.author }} · {{ book.category?.name || '未分类' }}</text>
      <text v-if="book.price != null" class="price">¥{{ book.price.toFixed(2) }}</text>
    </view>
  </view>
</template>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.book-card {
  background: $color-surface;
  border-radius: $radius-card;
  overflow: hidden;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.04);
}

.cover-wrap {
  position: relative;
  width: 100%;
  padding-top: 133%;
}

.cover {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
}

.badge {
  position: absolute;
  top: 12rpx;
  right: 12rpx;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  font-size: 20rpx;
  padding: 6rpx 12rpx;
  border-radius: 8rpx;
}

.info {
  padding: 16rpx 20rpx 20rpx;
}

.title {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
  line-height: 1.4;
}

.meta {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: $color-text-secondary;
}

.price {
  display: block;
  margin-top: 8rpx;
  color: $color-primary;
  font-weight: 600;
}
</style>
