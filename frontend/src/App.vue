<script setup lang="ts">
/**
 * 应用根组件
 *
 * 主布局：
 * 左侧：视频流 + 统计图表
 * 右侧：状态面板 + 语义面板 + 规则管理
 */
import { ref, onMounted, onUnmounted, computed } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import VideoStream from '@/components/VideoStream.vue'
import StatusPanel from '@/components/StatusPanel.vue'
import StatsChart from '@/components/StatsChart.vue'
import RuleManager from '@/components/RuleManager.vue'
import SemanticPanel from '@/components/SemanticPanel.vue'
import { useWebSocket } from '@/composables/useWebSocket'
import { useApi } from '@/composables/useApi'
import type { StatsResponse } from '@/types'
import StudyChatPanel from '@/components/StudyChatPanel.vue'

// WebSocket 连接 — 实时视频流 + 状态
const wsUrl = `ws://${window.location.hostname}:8000/ws/video`
const {
  isConnected,
  latestFrame,
  latestState,
  connect: wsConnect,
} = useWebSocket(wsUrl)

// API 调用
const { startCamera, getStats, startSession, resetSession, stopSession } = useApi()

// 统计数据与会话
const stats = ref<StatsResponse | null>(null)
let statsTimer: ReturnType<typeof setInterval>
const sessionActive = ref(false)
const finalStats = ref<StatsResponse | null>(null)

// 只给 box 调色：根据当前状态挂到最外层容器
const themeState = computed(() => {
  const state = latestState.value.state
  return ['专注', '分心', '低效', '离开'].includes(state) ? state : '未知'
})

/**
 * 启动摄像头并连接 WebSocket
 */
async function handleStartCamera() {
  await startCamera()
  wsConnect()
}

/**
 * 定期拉取统计数据
 */
async function refreshStats() {
  if (sessionActive.value) {
    const result = await getStats()
    if (result) stats.value = result
  }
}

// ─── 会话控制 ───
async function handleStartSession() {
  const result = await startSession()
  if (result) {
    sessionActive.value = true
    finalStats.value = null
    stats.value = null
  }
}

async function handleResetSession() {
  await resetSession()
  stats.value = null
  finalStats.value = null
  sessionActive.value = false
}

async function handleStopSession() {
  const result = await stopSession()
  if (result && result.stats) {
    sessionActive.value = false
    finalStats.value = result.stats
  }
}

onMounted(() => {
  wsConnect()
  refreshStats()
  statsTimer = setInterval(refreshStats, 3000)
})

onUnmounted(() => {
  clearInterval(statsTimer)
})
</script>

<template>
  <div class="study-shell" :data-study-state="themeState">
    <AppHeader :is-connected="isConnected" />

    <div class="app-layout">
      <!-- 左侧主区域 -->
      <div class="main-area">
       <VideoStream
       :frame="latestFrame"
       :is-connected="isConnected"
       @start-camera="handleStartCamera"
       />
       <StudyChatPanel :current-state="latestState" />
       <StatsChart :stats="stats" />
    </div>

      <!-- 右侧边栏 -->
      <div class="side-area">
        <div class="card session-controls">
          <div class="card-header">
            <span class="card-title">学习会话控制</span>
          </div>
          <div class="flex gap-2" style="margin-top: var(--space-3)">
            <button
              v-if="!sessionActive"
              class="btn btn-primary"
              @click="handleStartSession"
              style="flex: 1;"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke-width="1.5"
                stroke="currentColor"
                style="width: 16px; height: 16px;"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347c-.75.412-1.667-.13-1.667-.986V5.653z"
                />
              </svg>
              开始学习
            </button>

            <template v-else>
              <button class="btn btn-outline" @click="handleResetSession" style="flex: 1;">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke-width="1.5"
                  stroke="currentColor"
                  style="width: 16px; height: 16px;"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
                  />
                </svg>
                重置
              </button>

              <button class="btn btn-danger" @click="handleStopSession" style="flex: 1;">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke-width="1.5"
                  stroke="currentColor"
                  style="width: 16px; height: 16px;"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M5.25 7.5A2.25 2.25 0 017.5 5.25h9a2.25 2.25 0 012.25 2.25v9a2.25 2.25 0 01-2.25 2.25h-9a2.25 2.25 0 01-2.25-2.25v-9z"
                  />
                </svg>
                结束并分析
              </button>
            </template>
          </div>
        </div>

        <StatusPanel :state="latestState" />
        <SemanticPanel :current-state="latestState" />
        <RuleManager />
      </div>

      <!-- 弹窗：分析结果 -->
      <div v-if="finalStats" class="modal-overlay" @click.self="finalStats = null">
        <div class="modal card">
          <h2 class="modal-title">会话统计报告</h2>
          <div class="modal-grid">
            <div><strong class="text-secondary">总时长:</strong> {{ Math.floor(finalStats.totalDuration) }}s</div>
            <div><strong class="text-secondary">专注率:</strong> {{ finalStats.focusRate }}%</div>
            <div><strong class="text-secondary">专注时长:</strong> {{ Math.floor(finalStats.focusDuration) }}s</div>
            <div><strong class="text-secondary">分心时长:</strong> {{ Math.floor(finalStats.distractedDuration) }}s</div>
            <div><strong class="text-secondary">低效时长:</strong> {{ Math.floor(finalStats.lowEfficiencyDuration) }}s</div>
            <div><strong class="text-secondary">离开时长:</strong> {{ Math.floor(finalStats.awayDuration) }}s</div>
            <div><strong class="text-secondary">分心次数:</strong> {{ finalStats.distractedCount }} 次</div>
          </div>
          <button
            class="btn btn-primary"
            style="width: 100%; margin-top: var(--space-6);"
            @click="finalStats = null"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}

.modal {
  width: 400px;
  max-width: 90vw;
  box-shadow: var(--shadow-2);
}

.modal-title {
  margin-bottom: var(--space-4);
  color: var(--color-neutral-900);
}

.modal-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
  font-size: var(--text-base);
}
</style>