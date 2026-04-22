/**
 * 全局类型定义 — 与后端 Schema 对齐
 */

/** 单个检测目标 */
export interface DetectionItem {
  className: string
  confidence: number
  bbox: number[] // [x1, y1, x2, y2] 归一化坐标
  keypoints?: number[][] // [[x,y,conf], ...] 归一化坐标
}

/** 状态抽象结果 */
export interface AbstractedState {
  isPresent: boolean
  faceVisible: boolean
  headDown: boolean
  headTurnedAway: boolean
  postureStable: boolean
  stableDuration: number
  inactiveDuration: number
  awayDuration: number
}

/** 当前行为状态 */
export interface BehaviorState {
  state: string
  confidence: number
  stableDuration: number
  abstractedState: AbstractedState
  timestamp: number
}

/** WebSocket 推送的帧消息 */
export interface WsFrameMessage {
  type: 'frame'
  frame: string // base64 JPEG
  state: BehaviorState
  detections: DetectionItem[]
}

/** 学习行为统计 */
export interface StatsResponse {
  totalDuration: number
  focusDuration: number
  distractedDuration: number
  lowEfficiencyDuration: number
  awayDuration: number
  distractedCount: number
  phoneUsageDuration: number
  focusRate: number
  stateTimeline: StateTimelineItem[]
}

/** 状态时间线条目 */
export interface StateTimelineItem {
  state: string
  startTime: number
  endTime: number
  duration: number
}

/** 行为规则 */
export interface BehaviorRule {
  id: number
  ruleName: string
  conditionJson: string
  outputState: string
  enabled: boolean
  createdAt: string
}

/** 创建规则请求 */
export interface RuleCreateRequest {
  ruleName: string
  conditionJson: string
  outputState: string
}

/** 摄像头状态 */
export interface CameraStatus {
  running: boolean
  message: string
}

/** 语义解释请求 */
export interface SemanticExplainRequest {
  currentState: string
  abstractedState: AbstractedState
  matchedRule?: string
  context?: string
}

/** 语义解释响应 */
export interface SemanticExplainResponse {
  state: string
  explanation: string
  source: string
}

export interface ParsedRuleItem {
  ruleName: string
  conditionJson: string
  outputState: string
}

export interface NlRuleParseResponse {
  success: boolean
  parsedRule?: ParsedRuleItem
  error?: string
  rawText: string
}


export interface StudyChatRequest {
  message: string
  currentState: string
  stableDuration?: number
  abstractedState?: AbstractedState
}

export interface StudyChatResponse {
  reply: string
  source: string
  state?: string
  timestamp?: number
}

/** 学习状态常量 — 与后端对齐 */
export const STATE_LABELS: Record<string, string> = {
  '专注': '专注',
  '分心': '分心',
  '低效': '低效',
  '离开': '离开',
  '未知': '未知',
}

/** 状态对应的 CSS 类名 */
export const STATE_CSS_CLASS: Record<string, string> = {
  '专注': 'state-focus',
  '分心': 'state-distracted',
  '低效': 'state-low-efficiency',
  '离开': 'state-away',
  '未知': 'state-unknown',
}
