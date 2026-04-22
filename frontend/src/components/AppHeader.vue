<script setup lang="ts">
/**
 * 应用顶栏组件
 *
 * 展示系统名称、连接状态和当前时间
 */
import { ref, onMounted, onUnmounted } from 'vue'

defineProps<{
  isConnected: boolean
}>()

const currentTime = ref('')
let timer: ReturnType<typeof setInterval>

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', { hour12: false })
}

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  clearInterval(timer)
})
</script>

<template>
  <header class="app-header">
    <div class="header-left">
      <div class="logo">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="logo-icon">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
        </svg>
        <span class="logo-text">StudyMonitor</span>
      </div>
      <span class="header-subtitle">学习行为会话分析</span>
    </div>

    <div class="header-right">
      <div class="header-status">
        <span
          class="status-dot"
          :class="isConnected ? 'online' : 'offline'"
        />
        <span class="data-readout">
          {{ isConnected ? 'CONNECTED' : 'OFFLINE' }}
        </span>
      </div>
      <div class="header-time data-readout">
        <span class="value">{{ currentTime }}</span>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-6);
  background: var(--color-bg-surface);
  border-bottom: 1px solid var(--color-neutral-200);
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(12px);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.logo-icon {
  width: 20px;
  height: 20px;
  color: var(--color-neutral-900);
}

.logo-text {
  font-family: var(--font-artistic);
  font-size: var(--text-lg);
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--color-neutral-900);
}

.header-subtitle {
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
  padding-left: var(--space-4);
  border-left: 1px solid var(--color-neutral-200);
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-6);
}

.header-status {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.online {
  background: var(--color-success);
}

.status-dot.offline {
  background: var(--color-neutral-400);
}

.header-time {
  font-family: var(--font-data);
  font-size: var(--text-base);
  font-weight: 500;
  color: var(--color-neutral-900);
}
</style>
