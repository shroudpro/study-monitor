"""
Pydantic 请求/响应模型定义

NOTE: 所有 API 的输入输出都通过 Pydantic 校验，
确保数据格式正确且类型安全。
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ─── 检测相关 ───

class DetectionItem(BaseModel):
    """单个检测目标"""
    className: str
    confidence: float
    bbox: list[float] = Field(description="[x1, y1, x2, y2] 归一化坐标")
    keypoints: Optional[list[list[float]]] = Field(
        default=None, 
        description="[[x, y, conf], ...] 归一化关键点坐标"
    )


class DetectionResult(BaseModel):
    """一帧的检测结果"""
    detections: list[DetectionItem] = []
    frameTimestamp: float


# ─── 状态相关 ───

class AbstractedState(BaseModel):
    """
    状态抽象结果 — 基于上半身姿态的特征提取
    """
    isPresent: bool = False
    faceVisible: bool = False
    headDown: bool = False
    headTurnedAway: bool = False
    postureStable: bool = False
    stableDuration: float = 0.0
    inactiveDuration: float = 0.0
    awayDuration: float = 0.0

class BehaviorState(BaseModel):
    """当前行为状态（前端展示用）"""
    state: str = "unknown"
    confidence: float = 0.0
    stableDuration: float = 0.0
    abstractedState: AbstractedState = AbstractedState()
    timestamp: float = 0.0


# ─── 统计相关 ───

class StatsResponse(BaseModel):
    """学习行为统计响应"""
    totalDuration: float = Field(0, description="总监测时长（秒）")
    focusDuration: float = Field(0, description="专注时长（秒）")
    distractedDuration: float = Field(0, description="分心时长（秒）")
    lowEfficiencyDuration: float = Field(0, description="低效时长（秒）")
    awayDuration: float = Field(0, description="离开时长（秒）")
    distractedCount: int = Field(0, description="分心次数")
    phoneUsageDuration: float = Field(0, description="手机使用时长（秒）")
    focusRate: float = Field(0, description="专注率（%）")
    stateTimeline: list[dict] = Field([], description="状态时间线")


# ─── 规则相关 ───

class RuleCreate(BaseModel):
    """创建规则请求"""
    ruleName: str
    conditionJson: str = Field(description="JSON 格式的条件表达式")
    outputState: str


class RuleUpdate(BaseModel):
    """更新规则请求"""
    ruleName: Optional[str] = None
    conditionJson: Optional[str] = None
    outputState: Optional[str] = None
    enabled: Optional[bool] = None


class RuleResponse(BaseModel):
    """规则响应"""
    id: int
    ruleName: str
    conditionJson: str
    outputState: str
    enabled: bool
    createdAt: datetime

    class Config:
        from_attributes = True


# ─── 语义解释相关 ───

class SemanticExplainRequest(BaseModel):
    """语义解释请求"""
    currentState: str
    abstractedState: AbstractedState
    matchedRule: Optional[str] = None
    context: Optional[str] = None


class SemanticExplainResponse(BaseModel):
    """语义解释响应"""
    state: str
    explanation: str
    source: str = "vlm"


class NlRuleParseRequest(BaseModel):
    """自然语言规则解析请求"""
    ruleText: str


class ParsedRuleItem(BaseModel):
    ruleName: str
    conditionJson: str
    outputState: str


class NlRuleParseResponse(BaseModel):
    """自然语言规则解析响应"""
    success: bool
    parsedRule: Optional[ParsedRuleItem] = None
    error: Optional[str] = None
    rawText: str

class StudyChatRequest(BaseModel):
    """学习陪伴对话请求"""
    message: str
    currentState: str
    stableDuration: Optional[float] = None
    abstractedState: Optional[AbstractedState] = None


class StudyChatResponse(BaseModel):
    """学习陪伴对话响应"""
    reply: str
    source: str = "template"
    state: Optional[str] = None
    timestamp: Optional[float] = None





# ─── WebSocket 消息 ───

class WsFrameMessage(BaseModel):
    """WebSocket 推送给前端的帧消息"""
    type: str = "frame"
    frame: str = Field(description="base64 编码的 JPEG 图像")
    state: BehaviorState
    detections: list[DetectionItem] = []


# ─── 摄像头控制 ───

class CameraStatusResponse(BaseModel):
    """摄像头状态响应"""
    running: bool
    message: str
