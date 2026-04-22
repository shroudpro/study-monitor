/**
 * WebSocket 连接管理组合式函数
 *
 * NOTE: 自动重连机制 + 消息解析，确保与后端视频流的稳定连接
 */

import { ref, onUnmounted } from 'vue'
import type { WsFrameMessage, BehaviorState, DetectionItem } from '@/types'

export function useWebSocket(url: string) {
  const isConnected = ref(false)
  const latestFrame = ref('')
  const latestState = ref<BehaviorState>({
    state: '未知',
    confidence: 0,
    stableDuration: 0,
    abstractedState: {
      isPresent: false,
      faceVisible: false,
      headDown: false,
      headTurnedAway: false,
      postureStable: false,
      stableDuration: 0,
      inactiveDuration: 0,
      awayDuration: 0,
    },
    timestamp: 0,
  })
  const latestDetections = ref<DetectionItem[]>([])
  const error = ref<string | null>(null)

  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  const MAX_RECONNECT_DELAY = 5000

  /**
   * 建立 WebSocket 连接
   *
   * NOTE: 自动处理重连，指数退避策略
   */
  function connect() {
    if (ws?.readyState === WebSocket.OPEN) return

    try {
      ws = new WebSocket(url)

      ws.onopen = () => {
        isConnected.value = true
        error.value = null
      }

      ws.onmessage = (event: MessageEvent) => {
        try {
          const message: WsFrameMessage = JSON.parse(event.data)
          if (message.type === 'frame') {
            latestFrame.value = message.frame
            latestState.value = message.state
            latestDetections.value = message.detections
          }
        } catch {
          // 忽略非法消息格式
        }
      }

      ws.onclose = () => {
        isConnected.value = false
        // 自动重连
        scheduleReconnect()
      }

      ws.onerror = () => {
        error.value = 'WebSocket 连接失败'
        isConnected.value = false
      }
    } catch (e) {
      error.value = `WebSocket 创建失败: ${e}`
    }
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (ws) {
      ws.close()
      ws = null
    }
    isConnected.value = false
  }

  function scheduleReconnect() {
    if (reconnectTimer) return
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      connect()
    }, MAX_RECONNECT_DELAY)
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    latestFrame,
    latestState,
    latestDetections,
    error,
    connect,
    disconnect,
  }
}
