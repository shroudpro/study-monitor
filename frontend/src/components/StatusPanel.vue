<script setup lang="ts">
/**
 * 状态面板组件
 *
 * 展示当前学习状态（脉冲光晕指示器）和状态抽象详情
 */
import { computed } from 'vue'
import type { BehaviorState } from '@/types'
import { STATE_CSS_CLASS } from '@/types'

const props = defineProps<{
  state: BehaviorState
}>()

const stateClass = computed(() => {
  return STATE_CSS_CLASS[props.state.state] || 'state-unknown'
})

/**
 * 格式化持续时长为可读字符串
 */
function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.floor(seconds)}s`
  const min = Math.floor(seconds / 60)
  const sec = Math.floor(seconds % 60)
  return `${min}m ${sec}s`
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <span class="card-title">当前状态</span>
    </div>

    <!-- 主状态指示器 -->
    <div class="status-main">
      <div class="state-indicator" :class="stateClass">
        <span class="dot" />
        <span>{{ state.state }}</span>
      </div>
      <div class="status-duration data-readout">
        持续 <span class="value">{{ formatDuration(state.stableDuration) }}</span>
      </div>
    </div>

    <!-- 状态抽象详情 -->
    <div class="abstract-grid">
      <div class="abstract-item" :class="{ active: state.abstractedState.isPresent }">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="abstract-icon">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
        </svg>
        <span class="abstract-label">在场</span>
      </div>
      <div class="abstract-item" :class="{ active: state.abstractedState.faceVisible }">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="abstract-icon">
          <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <span class="abstract-label">脸部可见</span>
      </div>
      <div class="abstract-item" :class="{ active: state.abstractedState.headDown || state.abstractedState.headTurnedAway, warn: state.abstractedState.headDown || state.abstractedState.headTurnedAway }">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="abstract-icon">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
        </svg>
        <span class="abstract-label">动作偏移</span>
      </div>
      <div class="abstract-item" :class="{ active: state.abstractedState.postureStable }">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="abstract-icon">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="abstract-label">姿势稳定</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.status-main {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-6);
}

.abstract-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-2);
}

.abstract-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-bg-body);
  border: 1px solid var(--color-neutral-200);
  opacity: 0.6;
  transition: all var(--transition-fast);
}

.abstract-item.active {
  opacity: 1;
  border-color: var(--color-neutral-900);
  background: var(--color-bg-surface);
}

.abstract-item.warn {
  opacity: 1;
  border-color: var(--color-error);
  background: #fef2f2;
}

.abstract-icon {
  width: 16px;
  height: 16px;
  color: var(--color-neutral-500);
}

.abstract-item.active .abstract-icon {
  color: var(--color-neutral-900);
}

.abstract-item.warn .abstract-icon {
  color: var(--color-error);
}

.abstract-label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  color: var(--color-neutral-500);
}

.abstract-item.active .abstract-label {
  color: var(--color-neutral-900);
}

.abstract-item.warn .abstract-label {
  color: var(--color-error);
}
</style>
