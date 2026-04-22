"""
摄像头采集服务

NOTE: 使用 OpenCV 管理摄像头生命周期。
采用单例模式避免重复打开设备。
"""

import logging
import time
from typing import Optional

import cv2
import numpy as np

from app.config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS

logger = logging.getLogger(__name__)


class CameraService:
    """
    摄像头采集服务 — 负责打开/关闭摄像头、读取帧
    """

    def __init__(self) -> None:
        self._cap: Optional[cv2.VideoCapture] = None
        self._running: bool = False
        self._lastFrameTime: float = 0.0
        # 帧间隔（秒），控制最大帧率
        self._frameInterval: float = 1.0 / CAMERA_FPS

    @property
    def isRunning(self) -> bool:
        return self._running and self._cap is not None and self._cap.isOpened()

    def start(self) -> bool:
        """
        启动摄像头

        Returns:
            是否启动成功
        """
        if self.isRunning:
            logger.info("摄像头已在运行中")
            return True

        try:
            self._cap = cv2.VideoCapture(CAMERA_INDEX)
            if not self._cap.isOpened():
                logger.error(f"无法打开摄像头（索引: {CAMERA_INDEX}）")
                return False

            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            self._cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
            self._running = True
            logger.info(f"摄像头启动成功: {CAMERA_WIDTH}x{CAMERA_HEIGHT} @ {CAMERA_FPS}fps")
            return True
        except Exception as e:
            logger.error(f"摄像头启动失败: {e}")
            return False

    def stop(self) -> None:
        """释放摄像头资源"""
        self._running = False
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        logger.info("摄像头已停止")

    def readFrame(self) -> Optional[np.ndarray]:
        """
        读取一帧图像

        NOTE: 内部做了帧率控制，避免过快采集导致 CPU 占用过高

        Returns:
            BGR 格式的图像 ndarray，失败返回 None
        """
        if not self.isRunning:
            return None

        # 帧率控制
        now = time.time()
        elapsed = now - self._lastFrameTime
        if elapsed < self._frameInterval:
            return None

        ret, frame = self._cap.read()
        if not ret:
            logger.warning("读取摄像头帧失败")
            return None

        self._lastFrameTime = now
        return frame


# 全局单例
cameraService = CameraService()
