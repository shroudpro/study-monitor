"""
规则推理引擎 — 对应概要设计 2.3.3

NOTE: 显式规则系统，判定逻辑清晰且可解释。
支持默认规则 + 用户自定义规则（通过数据库加载）。
"""

import json
import logging
from typing import Optional

from app.schema.schemas import AbstractedState

logger = logging.getLogger(__name__)

# 学习行为状态常量
STATE_FOCUS = "专注"
STATE_DISTRACTED = "分心"
STATE_LOW_EFFICIENCY = "低效"
STATE_AWAY = "离开"
STATE_UNKNOWN = "未知"


class RuleEngine:
    """
    规则推理引擎

    基于状态抽象结果和时间信息，输出实时学习状态。
    支持两种规则来源：
    1. 内置默认规则（硬编码）
    2. 用户自定义规则（从数据库加载的 JSON 条件）
    """

    def __init__(self) -> None:
        self._customRules: list[dict] = []

    def loadCustomRules(self, rules: list[dict]) -> None:
        """
        从数据库加载用户自定义规则

        Args:
            rules: 规则字典列表，每项包含 conditionJson 和 outputState
        """
        self._customRules = rules
        logger.info(f"已加载 {len(rules)} 条自定义规则")

    def evaluate(self, state: AbstractedState) -> tuple[str, float]:
        """
        根据抽象状态执行规则推理

        NOTE: 规则优先级：
        1. 用户自定义规则（先匹配先生效）
        2. 内置默认规则（按固定优先级）

        Args:
            state: 状态抽象结果

        Returns:
            (行为状态, 置信度) 元组
        """
        # 先尝试用户自定义规则
        customResult = self._evaluateCustomRules(state)
        if customResult is not None:
            return customResult

        # 内置默认规则链（对应概要设计 2.3.3 的规则示例）
        return self._evaluateDefaultRules(state)

    def _evaluateDefaultRules(
        self, state: AbstractedState
    ) -> tuple[str, float]:
        """
        内置默认规则 — 基于人体姿态抽象及优先级重构
        
        优先级：
        1. 离开：not is_present 且 away_duration > 5.0
        2. 分心：is_present 且 head_turned_away 且 not head_down 且 stable_duration > 10.0
        3. 专注：双轨判定 (伏案 60s 或 屏幕 30s)
        4. 低效：兜底
        """
        
        # 1. 离开
        if not state.isPresent:
            if state.awayDuration > 5.0:
                return STATE_AWAY, 0.9
            else:
                return STATE_UNKNOWN, 0.5 # 还没满足离开时长

        # 2. 分心
        if state.headTurnedAway and not state.headDown and state.stableDuration > 10.0:
            return STATE_DISTRACTED, 0.85
        elif state.headTurnedAway and not state.headDown:
            return STATE_DISTRACTED, 0.5

        # 3. 专注 (双轨判定)
        # A. 伏案专注: 允许 60s 静止
        if state.headDown and state.inactiveDuration <= 60.0:
            return STATE_FOCUS, 0.85
            
        # B. 屏幕专注: 允许 30s 静止
        if not state.headDown and not state.headTurnedAway and state.inactiveDuration <= 30.0:
            return STATE_FOCUS, 0.85

        # 4. 兜底为低效
        # 这会落入：死盯着屏幕>30s不动，或伏案>60s不动等极端情况
        return STATE_LOW_EFFICIENCY, 0.8

    def _evaluateCustomRules(
        self, state: AbstractedState
    ) -> Optional[tuple[str, float]]:
        """
        执行用户自定义规则

        NOTE: 自定义规则以 JSON 条件格式存储，格式示例：
        {
            "using_phone": true,
            "duration_sec": {">": 10}
        }
        """
        for rule in self._customRules:
            try:
                condition = json.loads(rule.get("conditionJson", "{}"))
                if self._matchCondition(condition, state):
                    return rule.get("outputState", STATE_UNKNOWN), 0.7
            except json.JSONDecodeError:
                logger.warning(f"规则条件 JSON 解析失败: {rule.get('ruleName')}")
                continue

        return None

    def _matchCondition(
        self, condition: dict, state: AbstractedState
    ) -> bool:
        """
        匹配单条规则的条件

        支持的条件字段：
        - is_present, face_visible, head_down, head_turned_away, posture_stable: bool
        - duration_sec: 支持 ">", "<", ">=" 等比较操作
        """
        fieldMapping = {
            "is_present": state.isPresent,
            "face_visible": state.faceVisible,
            "head_down": state.headDown,
            "head_turned_away": state.headTurnedAway,
            "posture_stable": state.postureStable,
        }

        for key, expected in condition.items():
            if key == "duration_sec":
                # 时长条件是一个比较表达式
                if isinstance(expected, dict):
                    for op, val in expected.items():
                        if op == ">" and not (state.stableDuration > val):
                            return False
                        elif op == ">=" and not (state.stableDuration >= val):
                            return False
                        elif op == "<" and not (state.stableDuration < val):
                            return False
                        elif op == "<=" and not (state.stableDuration <= val):
                            return False
            elif key in fieldMapping:
                if fieldMapping[key] != expected:
                    return False

        return True


# 全局单例
ruleEngine = RuleEngine()
