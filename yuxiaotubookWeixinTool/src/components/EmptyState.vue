<script setup lang="ts">
defineProps<{
  text?: string
  actionText?: string
}>()

const emit = defineEmits<{ action: [] }>()
</script>

<template>
  <view class="empty-state">
    <text class="icon">📚</text>
    <text class="text">{{ text || '暂无内容' }}</text>
    <button v-if="actionText" class="action" @tap="emit('action')">{{ actionText }}</button>
  </view>
</template>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.empty-state {
  padding: 100rpx 40rpx;
  text-align: center;
}

.icon {
  display: block;
  font-size: 64rpx;
  margin-bottom: 20rpx;
}

.text {
  color: $color-text-secondary;
  font-size: 28rpx;
}

.action {
  margin-top: 32rpx;
  background: $color-primary;
  color: #fff;
  font-size: 28rpx;
}
</style>
