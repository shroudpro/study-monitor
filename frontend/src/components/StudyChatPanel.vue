<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { useApi } from '@/composables/useApi'
import type { BehaviorState } from '@/types'

const props = defineProps<{
  currentState?: BehaviorState
}>()

type ChatMessage = {
  id: number
  role: 'assistant' | 'user'
  content: string
  source?: string
}

const { sendStudyChat } = useApi()

const input = ref('')
const loading = ref(false)
const messages = ref<ChatMessage[]>([])
const distractionNudgeTriggered = ref(false)
let interruptionAudio: HTMLAudioElement | null = null

const DISTRACTION_THRESHOLD_SEC = 120
const DISTRACTION_NUDGE_TEXT = '小帅小帅，走神了吗，要不先休息几分钟，我陪你聊聊天'

const stateLabel = computed(() => props.currentState?.state || '未知')

const placeholderText = computed(() => {
  return '这里现在是普通文本对话。你可以直接打招呼、提问，或随便聊一句。'
})

function pushUserMessage(content: string) {
  messages.value.push({
    id: Date.now() + Math.random(),
    role: 'user',
    content,
  })
}

function pushAssistantMessage(content: string, source = 'template') {
  messages.value.push({
    id: Date.now() + Math.random(),
    role: 'assistant',
    content,
    source,
  })
}

function playInterruptionAudio() {
  if (!interruptionAudio) {
    interruptionAudio = new Audio('/api/assets/interruption-audio')
    interruptionAudio.preload = 'auto'
  }

  interruptionAudio.currentTime = 0
  interruptionAudio.play().catch((error) => {
    console.warn('分心提醒音频播放失败，可能需要用户先与页面交互。', error)
  })
}

function triggerDistractionNudge() {
  distractionNudgeTriggered.value = true
  playInterruptionAudio()
  pushAssistantMessage(DISTRACTION_NUDGE_TEXT, 'distraction-nudge')
}

watch(
  () => ({
    state: props.currentState?.state,
    stableDuration: props.currentState?.stableDuration ?? 0,
  }),
  ({ state, stableDuration }) => {
    if (state !== '分心') {
      distractionNudgeTriggered.value = false
      return
    }

    if (
      stableDuration > DISTRACTION_THRESHOLD_SEC &&
      !distractionNudgeTriggered.value
    ) {
      triggerDistractionNudge()
    }
  },
  { immediate: true }
)

onUnmounted(() => {
  if (interruptionAudio) {
    interruptionAudio.pause()
    interruptionAudio = null
  }
})

async function handleSend() {
  const content = input.value.trim()
  if (!content || loading.value) return

  pushUserMessage(content)
  input.value = ''
  loading.value = true

  const result = await sendStudyChat({
    message: content,
    currentState: stateLabel.value,
    stableDuration: props.currentState?.stableDuration,
    abstractedState: props.currentState?.abstractedState,
  })

  loading.value = false

  if (result?.reply) {
    pushAssistantMessage(result.reply, result.source)
  } else {
    pushAssistantMessage('当前本地模型暂时不可用，请确认 Ollama 已启动后再试一次。', 'fallback')
  }
}
</script>

<template>
  <div class="card study-chat-panel">
    <div class="card-header">
      <span class="card-title">学习陪伴对话</span>
      <span class="chat-state-badge">{{ stateLabel }}</span>
    </div>

    <div class="chat-panel-body">
      <template v-if="messages.length === 0 && !loading">
        <div class="chat-placeholder">
          {{ placeholderText }}
        </div>
      </template>

      <div v-else class="chat-messages">
        <div
          v-for="message in messages"
          :key="message.id"
          class="chat-message"
          :class="message.role"
        >
          {{ message.content }}
        </div>

        <div v-if="loading" class="chat-loading">
          <span class="chat-spinner"></span>
          <span>正在生成回复...</span>
        </div>
      </div>
    </div>

    <div class="chat-input-row">
      <input
        v-model="input"
        class="input"
        type="text"
        placeholder="输入内容，例如：你好，今天想聊点什么？"
        :disabled="loading"
        @keyup.enter="handleSend"
      />
      <button class="btn btn-primary" :disabled="loading || !input.trim()" @click="handleSend">
        {{ loading ? '生成中' : '发送' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.study-chat-panel {
  min-height: 300px;
}

.chat-state-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 72px;
  height: 36px;
  padding: 0 14px;
  border-radius: 999px;
  background: var(--study-accent-soft, rgba(156, 163, 175, 0.12));
  border: 1px solid var(--study-accent-border, rgba(156, 163, 175, 0.28));
  color: var(--study-accent-strong, #6b7280);
  font-size: var(--text-sm);
  font-weight: 600;
}

.chat-panel-body {
  min-height: 150px;
  margin-bottom: var(--space-4);
}

.chat-placeholder {
  min-height: 130px;
  border: 1px dashed var(--study-accent-border, rgba(156, 163, 175, 0.28));
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.72);
  padding: var(--space-4);
  color: var(--color-neutral-500);
  display: flex;
  align-items: center;
  line-height: 1.8;
}

.chat-messages {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.chat-message {
  max-width: 88%;
  padding: 12px 14px;
  border-radius: 12px;
  line-height: 1.7;
  font-size: var(--text-sm);
  word-break: break-word;
}

.chat-message.user {
  align-self: flex-end;
  background: var(--study-accent-soft, rgba(156, 163, 175, 0.12));
  border: 1px solid var(--study-accent-border, rgba(156, 163, 175, 0.28));
  color: var(--color-neutral-900);
}

.chat-message.assistant {
  align-self: flex-start;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid var(--color-neutral-200);
  color: var(--color-neutral-800);
}

.chat-loading {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--color-neutral-500);
  font-size: var(--text-sm);
  padding: 4px 2px;
}

.chat-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--study-accent-border, rgba(156, 163, 175, 0.28));
  border-top-color: var(--study-accent, #9ca3af);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.chat-input-row {
  display: flex;
  gap: var(--space-3);
}

.chat-input-row .input {
  flex: 1;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
