"""
时间序列分析服务 — 对应概要设计 2.3.4

NOTE: 使用滑动窗口记录状态变化，对行为做持续性分析，
降低 YOLO 瞬时误判带来的状态频繁跳变。
"""

import logging
import time
from collections import deque, Counter
from typing import Optional

from app.config import SLIDING_WINDOW_SIZE, STATE_CHANGE_THRESHOLD

logger = logging.getLogger(__name__)


class TimelineService:
    """
    时间序列分析模块

    通过滑动窗口平滑状态判定：
    - 记录最近 N 帧的状态
    - 只有当新状态连续出现达到阈值时，才真正切换
    - 计算当前状态的持续时长
    """

    def __init__(self) -> None:
        # 滑动窗口，存储 (状态, 时间戳) 元组
        self._window: deque[tuple[str, float]] = deque(
            maxlen=SLIDING_WINDOW_SIZE
        )
        # 当前确认的稳定状态
        self._currentState: str = "未知"
        # 当前状态起始时间
        self._stateStartTime: float = time.time()
        # 监测起始时间
        self._monitorStartTime: float = 0.0
        # 状态变更历史（用于统计）
        self._stateHistory: list[dict] = []
        # 会话运行标志
        self._isRunning = False

    @property
    def currentState(self) -> str:
        return self._currentState

    @property
    def isRunning(self) -> bool:
        return self._isRunning

    @property
    def stableDuration(self) -> float:
        """当前状态的持续时长（秒）"""
        if not self._isRunning:
            return 0.0
        return time.time() - self._stateStartTime

    @property
    def totalDuration(self) -> float:
        """总监测时长（秒）"""
        if not self._isRunning:
            return 0.0
        return time.time() - self._monitorStartTime

    def update(self, rawState: str) -> str:
        """
        更新状态序列并返回平滑后的稳定状态

        NOTE: 平滑逻辑 —
        在滑动窗口中，只有当新状态出现次数超过阈值时才切换。
        这样可以避免检测偶尔漏检/误检导致的状态抖动。

        Args:
            rawState: 规则引擎输出的原始状态

        Returns:
            平滑后的稳定状态
        """
        if not self._isRunning:
            return self._currentState

        now = time.time()
        self._window.append((rawState, now))

        # 统计窗口内各状态出现次数
        stateCounts = Counter(state for state, _ in self._window)
        mostCommon = stateCounts.most_common(1)[0]
        dominantState = mostCommon[0]
        dominantCount = mostCommon[1]

        # 只有当主导状态出现次数超过阈值时才切换
        if (dominantState != self._currentState and
                dominantCount >= STATE_CHANGE_THRESHOLD):
            # 记录前一个状态段
            self._stateHistory.append({
                "state": self._currentState,
                "startTime": self._stateStartTime,
                "endTime": now,
                "duration": now - self._stateStartTime,
            })

            self._currentState = dominantState
            self._stateStartTime = now
            logger.debug(f"状态切换: → {dominantState}")

        return self._currentState

    def getStableDurationForState(self, rawState: str) -> float:
        """
        获取指定原始状态在窗口内的连续时长

        NOTE: 用于传递给规则引擎，让规则引擎可以使用 duration 条件
        """
        if not self._window:
            return 0.0

        # 从窗口尾部向前数，找到连续相同状态的起始时间
        duration = 0.0
        for state, ts in reversed(self._window):
            if state == rawState:
                if duration == 0.0:
                    duration = time.time() - ts
                else:
                    duration = time.time() - ts
            else:
                break

        return duration

    def getStateHistory(self) -> list[dict]:
        """获取完整的状态变更历史"""
        # 加上当前正在进行的状态段
        history = list(self._stateHistory)
        history.append({
            "state": self._currentState,
            "startTime": self._stateStartTime,
            "endTime": time.time(),
            "duration": self.stableDuration,
        })
        return history

    def reset(self) -> None:
        """重置所有状态（暂不启动）"""
        self._window.clear()
        self._currentState = "未知"
        self._stateHistory.clear()
        logger.info("时间序列分析已重置")

    def startSession(self) -> None:
        """开始新的 session"""
        self.reset()
        now = time.time()
        self._stateStartTime = now
        self._monitorStartTime = now
        self._isRunning = True
        logger.info("学习 Session 已开始")

    def stopSession(self) -> None:
        """停止当前 session"""
        if self._isRunning:
            self._isRunning = False
            # 记录最后一段
            now = time.time()
            if self._currentState != "未知":
                self._stateHistory.append({
                    "state": self._currentState,
                    "startTime": self._stateStartTime,
                    "endTime": now,
                    "duration": now - self._stateStartTime,
                })
            logger.info("学习 Session 已停止")


# 全局单例
timelineService = TimelineService()
