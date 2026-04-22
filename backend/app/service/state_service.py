"""
状态抽象服务 — 对应概要设计 2.3.2

NOTE: 这是系统从「视觉检测」走向「行为推理」的桥梁。
将 YOLO 低层检测结果转换为高层语义状态。
"""

import logging
import math
from collections import deque

from app.schema.schemas import DetectionItem, AbstractedState

logger = logging.getLogger(__name__)


class StateService:
    """
    状态抽象模块

    利用 YOLO Pose 的 17 个关键点提取：
    - isPresent: 是否有人
    - faceVisible: 是否能看到正脸（眼睛、鼻子）
    - headDown: 是否低头
    - headTurnedAway: 是否转头
    - postureStable: 姿态是否稳定
    """

    def __init__(self):
        # 缓存最后几帧的肩膀中心和鼻子坐标，用于计算平稳度
        # [[(nose_x, nose_y), (shoulder_cx, shoulder_cy)], ...]
        self._history_poses = deque(maxlen=15)
        import time
        now = time.time()
        self._inactive_start = now
        self._away_start = now

    def abstract(
        self,
        detections: list[DetectionItem],
        stableDuration: float = 0.0,
    ) -> AbstractedState:
        """
        从一帧检测结果中抽象出语义状态
        """
        import time
        now = time.time()
        if not detections:
            self._history_poses.clear()
            self._inactive_start = now # 不在位时不统计发呆
            return AbstractedState(
                isPresent=False,
                awayDuration=now - self._away_start,
                stableDuration=stableDuration
            )

        # 取置信度最高的 person
        person = max(detections, key=lambda d: d.confidence)
        isPresent = True
        self._away_start = now
        awayDuration = 0.0
        
        # 默认状态
        faceVisible = False
        headDown = False
        headTurnedAway = False
        postureStable = False
        inactiveDuration = 0.0

        if not person.keypoints or len(person.keypoints) < 17:
            self._inactive_start = now
            return AbstractedState(
                isPresent=True, stableDuration=stableDuration
            )

        kpts = person.keypoints
        nose = kpts[0]
        l_eye, r_eye = kpts[1], kpts[2]
        l_ear, r_ear = kpts[3], kpts[4]
        l_shoulder, r_shoulder = kpts[5], kpts[6]

        # 判断 faceVisible: 鼻子置信度高，且至少一只眼睛可见
        if nose[2] > 0.5 and (l_eye[2] > 0.5 or r_eye[2] > 0.5):
            faceVisible = True

        # 判断 headTurnedAway: 两只耳朵的置信度，或者鼻子与两耳的距离不对称
        # 如果只有一只耳朵可见，大概率是严重侧头
        if (l_ear[2] > 0.4 and r_ear[2] < 0.2) or (r_ear[2] > 0.4 and l_ear[2] < 0.2):
            headTurnedAway = True
            faceVisible = False # 严重侧头等于看不到正脸

        # 判断 headDown: 鼻子到肩膀中点的距离很短，或者只看到头顶(眼睛/鼻子不可见，只有耳朵或肩膀)
        shoulder_cy = -1
        if l_shoulder[2] > 0.5 and r_shoulder[2] > 0.2:
            shoulder_cx = (l_shoulder[0] + r_shoulder[0]) / 2
            shoulder_cy = (l_shoulder[1] + r_shoulder[1]) / 2
            
            # 记录历史轨迹
            if nose[2] > 0.5:
                self._history_poses.append(((nose[0], nose[1]), (shoulder_cx, shoulder_cy)))
            
            if nose[2] > 0.5:
                # 鼻子距离肩膀的垂直距离通常占图像一段比例，如果很小说明低下了头，或者趴着
                if (shoulder_cy - nose[1]) < 0.05: 
                    headDown = True
        
        # 兜底判断低头：如果没有鼻子但看到了肩膀和耳朵
        if nose[2] < 0.2 and shoulder_cy > 0:
            headDown = True

        # 计算姿态稳定性与 inactive (判断是否在发呆/乱动)
        # 将阈值从 0.01 收紧到 0.0005，使得微小的晃动也会被识别为活动
        if len(self._history_poses) >= 10:
            nose_xs = [p[0][0] for p in self._history_poses]
            nose_ys = [p[0][1] for p in self._history_poses]
            sh_xs = [p[1][0] for p in self._history_poses]
            sh_ys = [p[1][1] for p in self._history_poses]
            
            var_nx = self._variance(nose_xs)
            var_ny = self._variance(nose_ys)
            var_sx = self._variance(sh_xs)
            var_sy = self._variance(sh_ys)
            
            total_variance = var_nx + var_ny + var_sx + var_sy
            
            # 阈值收紧至 0.0005 (原为 0.01)
            if total_variance < 0.0005:
                postureStable = True
                inactiveDuration = now - self._inactive_start
            else:
                postureStable = False
                self._inactive_start = now
                inactiveDuration = 0.0
        else:
            # 样本不够时，默认认为当前处于活动/不稳定状态，避免刚开始就判定为静止
            postureStable = False
            self._inactive_start = now
            inactiveDuration = 0.0

        return AbstractedState(
            isPresent=isPresent,
            faceVisible=faceVisible,
            headDown=headDown,
            headTurnedAway=headTurnedAway,
            postureStable=postureStable,
            stableDuration=stableDuration,
            inactiveDuration=inactiveDuration,
            awayDuration=awayDuration,
        )

    def _variance(self, values: list[float]) -> float:
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)


# 全局单例
stateService = StateService()
