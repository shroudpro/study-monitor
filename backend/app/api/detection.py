"""
检测相关 API 路由

包含状态查询接口，检测主循环在 WebSocket 中运行。
"""

import logging

from fastapi import APIRouter

from app.schema.schemas import BehaviorState, CameraStatusResponse
from app.service.camera_service import cameraService
from app.service.timeline_service import timelineService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["detection"])


@router.get("/state", response_model=BehaviorState)
async def getCurrentState():
    """
    获取当前行为状态

    NOTE: 状态由 WebSocket 主循环持续更新，
    此接口仅读取最新的稳定状态。
    """
    import time
    return BehaviorState(
        state=timelineService.currentState,
        confidence=0.8,
        stableDuration=round(timelineService.stableDuration, 1),
        timestamp=time.time(),
    )


@router.post("/camera/start", response_model=CameraStatusResponse)
async def startCamera():
    """启动摄像头"""
    success = cameraService.start()
    return CameraStatusResponse(
        running=success,
        message="摄像头启动成功" if success else "摄像头启动失败，请检查设备连接",
    )


@router.post("/camera/stop", response_model=CameraStatusResponse)
async def stopCamera():
    """停止摄像头"""
    cameraService.stop()
    return CameraStatusResponse(
        running=False,
        message="摄像头已停止",
    )
