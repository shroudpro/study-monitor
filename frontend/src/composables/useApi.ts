/**
 * API 调用组合式函数
 *
 * NOTE: 封装所有 REST API 调用，统一错误处理
 */

import { ref } from 'vue'
import type {
  StatsResponse,
  BehaviorRule,
  RuleCreateRequest,
  CameraStatus,
  SemanticExplainResponse,
  SemanticExplainRequest,
  NlRuleParseResponse,
  StudyChatRequest,
  StudyChatResponse,
} from '@/types'

const API_BASE = '/api'

/**
 * 通用请求封装
 */
async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`)
  }
  return response.json()
}

export function useApi() {
  const loading = ref(false)
  const apiError = ref<string | null>(null)

  // ─── 摄像头控制 ───

  async function startCamera(): Promise<CameraStatus> {
    loading.value = true
    try {
      const result = await request<CameraStatus>('/camera/start', { method: 'POST' })
      apiError.value = null
      return result
    } catch (e) {
      apiError.value = `启动摄像头失败: ${e}`
      return { running: false, message: apiError.value }
    } finally {
      loading.value = false
    }
  }

  async function stopCamera(): Promise<CameraStatus> {
    loading.value = true
    try {
      const result = await request<CameraStatus>('/camera/stop', { method: 'POST' })
      apiError.value = null
      return result
    } catch (e) {
      apiError.value = `停止摄像头失败: ${e}`
      return { running: false, message: apiError.value }
    } finally {
      loading.value = false
    }
  }

  // ─── 会话与统计 ───

  async function startSession(): Promise<{ sessionId: string } | null> {
    try {
      return await request<{ sessionId: string }>('/session/start', { method: 'POST' })
    } catch (e) {
      apiError.value = `启动会话失败: ${e}`
      return null
    }
  }

  async function resetSession(): Promise<{ status: string } | null> {
    try {
      return await request<{ status: string }>('/session/reset', { method: 'POST' })
    } catch (e) {
      apiError.value = `重置会话失败: ${e}`
      return null
    }
  }

  async function stopSession(): Promise<{ status: string, stats?: StatsResponse } | null> {
    try {
      return await request<{ status: string, stats?: StatsResponse }>('/session/stop', { method: 'POST' })
    } catch (e) {
      apiError.value = `停止会话失败: ${e}`
      return null
    }
  }

  async function getStats(): Promise<StatsResponse | null> {
    try {
      return await request<StatsResponse>('/stats')
    } catch (e) {
      apiError.value = `获取统计失败: ${e}`
      return null
    }
  }

  // ─── 规则管理 ───

  async function getRules(): Promise<BehaviorRule[]> {
    try {
      return await request<BehaviorRule[]>('/rules')
    } catch (e) {
      apiError.value = `获取规则失败: ${e}`
      return []
    }
  }

  async function createRule(rule: RuleCreateRequest): Promise<BehaviorRule | null> {
    try {
      return await request<BehaviorRule>('/rules', {
        method: 'POST',
        body: JSON.stringify(rule),
      })
    } catch (e) {
      apiError.value = `创建规则失败: ${e}`
      return null
    }
  }

  async function deleteRule(ruleId: number): Promise<boolean> {
    try {
      await request(`/rules/${ruleId}`, { method: 'DELETE' })
      return true
    } catch (e) {
      apiError.value = `删除规则失败: ${e}`
      return false
    }
  }

  async function toggleRule(ruleId: number, enabled: boolean): Promise<boolean> {
    try {
      await request(`/rules/${ruleId}`, {
        method: 'PUT',
        body: JSON.stringify({ enabled }),
      })
      return true
    } catch (e) {
      apiError.value = `更新规则失败: ${e}`
      return false
    }
  }

  // ─── 语义解释 ───

  async function getExplanation(requestData: SemanticExplainRequest): Promise<SemanticExplainResponse | null> {
    try {
      return await request<SemanticExplainResponse>('/semantic/explain', {
        method: 'POST',
        body: JSON.stringify(requestData),
      })
    } catch (e) {
      apiError.value = `获取解释失败: ${e}`
      return null
    }
  }

  async function parseNlRule(ruleText: string): Promise<NlRuleParseResponse | null> {
    loading.value = true
    try {
      return await request<NlRuleParseResponse>('/semantic/rules/parse', {
        method: 'POST',
        body: JSON.stringify({ ruleText }),
      })
    } catch (e) {
      apiError.value = `解析规则失败: ${e}`
      return null
    } finally {
      loading.value = false
    }
  }

    async function sendStudyChat(payload: StudyChatRequest): Promise<StudyChatResponse | null> {
    loading.value = true
    try {
      return await request<StudyChatResponse>('/semantic/chat', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
    } catch (e) {
      apiError.value = `学习对话失败: ${e}`
      return null
    } finally {
      loading.value = false
    }
  }



  return {
    loading,
    apiError,
    startCamera,
    stopCamera,
    startSession,
    resetSession,
    stopSession,
    getStats,
    getRules,
    createRule,
    deleteRule,
    toggleRule,
    getExplanation,
    parseNlRule,
    sendStudyChat,
  }
}
