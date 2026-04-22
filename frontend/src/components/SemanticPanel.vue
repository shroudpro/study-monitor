<script setup lang="ts">
/**
 * 语义解释面板组件
 *
 * 状态变化时自动调用 VLM 生成解释，并展示历史时间线
 */
import { ref, watch } from 'vue'
import { useApi } from '@/composables/useApi'
import type { BehaviorState, SemanticExplainResponse } from '@/types'

const props = defineProps<{
  currentState: BehaviorState
}>()

const { getExplanation } = useApi()

interface HistoryItem {
  time: string
  state: string
  explanation: string
  source: string
}

const explanation = ref<SemanticExplainResponse | null>(null)
const history = ref<HistoryItem[]>([])
const loading = ref(false)

// 监听状态变化，当平滑后的状态发生变化时，请求解释
watch(() => props.currentState.state, async (newState, oldState) => {
  if (newState === oldState || newState === '未知') return
  await fetchExplanation()
})

async function fetchExplanation() {
  loading.value = true
  const res = await getExplanation({
    currentState: props.currentState.state,
    abstractedState: props.currentState.abstractedState,
  })
  loading.value = false
  if (res) {
    explanation.value = res
    // 加入历史记录
    history.value.unshift({
      time: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
      state: res.state,
      explanation: res.explanation,
      source: res.source
    })
    // 保持最多 10 条历史
    if (history.value.length > 10) history.value.pop()
  }
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <span class="card-title">行为解释</span>
      <button v-if="explanation" class="btn btn-sm btn-outline" @click="fetchExplanation" :disabled="loading">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 14px; height: 14px;">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
        </svg>
      </button>
    </div>

    <div class="current-explanation">
      <div v-if="loading" class="text-secondary text-sm text-center py-4">正在生成解释...</div>
      <div v-else-if="explanation" class="semantic-text animate-fade-in">
        <div class="state-title text-sm flex items-center justify-between">
          <span><strong>当前：</strong><span :class="'state-text-' + explanation.state">{{ explanation.state }}</span></span>
          <span class="tag" :class="explanation.source === 'vlm' ? 'tag-vlm' : 'tag-template'">{{ explanation.source === 'vlm' ? 'VLM' : '模板' }}</span>
        </div>
        <p class="explanation-content text-sm mt-2 font-data text-secondary">"{{ explanation.explanation }}"</p>
      </div>
      <div v-else class="semantic-placeholder text-center py-4">
        <p class="text-sm text-secondary">等待状态稳定后自动解释...</p>
      </div>
    </div>

    <div v-if="history.length > 0" class="history-timeline mt-4 pt-4">
      <div class="history-title text-xs text-tertiary mb-2 text-center">── 行为历史 ──</div>
      <div class="history-list">
        <div v-for="(item, idx) in history" :key="idx" class="history-item mb-3">
          <div class="history-meta text-xs flex items-center justify-between">
            <span class="text-tertiary font-data">{{ item.time }}</span>
            <span :class="'text-xs state-text-' + item.state"><strong>{{ item.state }}</strong></span>
          </div>
          <p class="history-content text-xs text-secondary mt-1 ml-2 border-l-2 border-neutral-200 pl-2">
            "{{ item.explanation }}"
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.py-4 { padding-top: var(--space-4); padding-bottom: var(--space-4); }
.mt-4 { margin-top: var(--space-4); }
.pt-4 { padding-top: var(--space-4); border-top: 1px solid var(--color-neutral-200); }
.mb-2 { margin-bottom: var(--space-2); }
.mb-3 { margin-bottom: var(--space-3); }
.mt-1 { margin-top: var(--space-1); }
.mt-2 { margin-top: var(--space-2); }
.ml-2 { margin-left: var(--space-2); }
.pl-2 { padding-left: var(--space-2); }
.border-l-2 { border-left-width: 2px; border-left-style: solid; }
.border-neutral-200 { border-color: var(--color-neutral-200); }

.history-list {
  max-height: 200px;
  overflow-y: auto;
}

.history-list::-webkit-scrollbar {
  width: 4px;
}
.history-list::-webkit-scrollbar-thumb {
  background: var(--color-neutral-300);
  border-radius: 4px;
}

.state-text-专注 { color: var(--color-success); }
.state-text-分心 { color: var(--color-error); }
.state-text-低效 { color: var(--color-warning); }
.state-text-离开 { color: var(--color-neutral-500); }

.tag-vlm {
  background-color: var(--color-primary);
  color: white;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
}

.tag-template {
  background-color: var(--color-neutral-200);
  color: var(--color-neutral-600);
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
}
</style>
