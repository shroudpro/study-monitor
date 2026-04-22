"""
FastAPI 应用入口

NOTE: 系统核心调度中心，包含：
1. CORS 配置（允许前端跨域访问）
2. 路由挂载
3. 启动事件（初始化数据库、加载模型）
4. WebSocket 端点（实时推送检测帧 + 状态）
"""

import asyncio
import base64
import json
import logging
import time
from pathlib import Path

import cv2
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import API_HOST, API_PORT, WS_PUSH_INTERVAL_MS
from app.database import initDb
from app.api import detection, stats, rules, semantic
from app.service.camera_service import cameraService
from app.service.detector_service import detectorService
from app.service.state_service import stateService
from app.service.rule_engine import ruleEngine
from app.service.timeline_service import timelineService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
BACKEND_ROOT = Path(__file__).resolve().parents[1]
INTERRUPTION_AUDIO_PATH = BACKEND_ROOT / "interrupt.mp3"


# ─── 创建 FastAPI 应用 ───
app = FastAPI(
    title="学习行为视觉规则推理系统",
    description="本地离线运行的智能学习行为分析 API",
    version="1.0.0-mvp",
)

# CORS 配置 — 允许本地前端开发服务器访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── 挂载路由 ───
app.include_router(detection.router)
app.include_router(stats.router)
app.include_router(rules.router)
app.include_router(semantic.router)


# ─── 启动事件 ───
@app.on_event("startup")
async def onStartup():
    """
    应用启动时初始化：
    1. 创建/检查数据库表
    2. 加载 YOLO 模型
    """
    logger.info("正在初始化系统...")

    # 初始化数据库
    initDb()
    logger.info("数据库初始化完成")

    # 加载 YOLO 模型
    if detectorService.loadModel():
        logger.info("YOLO 模型加载完成")
    else:
        logger.warning(
            "YOLO 模型未加载 — 系统将以模拟模式运行。"
            "请下载 yolov8n.onnx 到 backend/models/ 目录"
        )

    logger.info("系统初始化完成")


@app.on_event("shutdown")
async def onShutdown():
    """应用关闭时释放资源"""
    cameraService.stop()
    logger.info("系统已关闭")


# ─── WebSocket 端点：实时视频推送 ───
@app.websocket("/ws/video")
async def videoWebsocket(websocket: WebSocket):
    """
    实时视频流 WebSocket

    NOTE: 这是整个系统的核心实时链路：
    摄像头采集 → YOLO 检测 → 状态抽象 → 规则推理 → 时间序列平滑 → 推送前端

    推送消息格式 (JSON):
    {
        "type": "frame",
        "frame": "<base64 JPEG>",
        "state": { ... BehaviorState ... },
        "detections": [ ... DetectionItem ... ]
    }
    """
    await websocket.accept()
    logger.info("WebSocket 客户端已连接")

    # 自动启动摄像头
    if not cameraService.isRunning:
        cameraService.start()

    pushInterval = WS_PUSH_INTERVAL_MS / 1000.0

    try:
        while True:
            frame = cameraService.readFrame()

            if frame is not None:
                # ── 实时检测链路 ──
                detections = []
                if detectorService.isLoaded:
                    detections = detectorService.detect(frame)

                # 状态抽象
                # NOTE: 先获取当前原始状态的持续时长，用于规则引擎判断
                rawDuration = timelineService.stableDuration
                abstractedState = stateService.abstract(detections, rawDuration)

                # 规则推理
                rawState, confidence = ruleEngine.evaluate(abstractedState)

                # 时间序列平滑
                smoothedState = timelineService.update(rawState)

                # 在帧上绘制检测框
                if detectorService.isLoaded:
                    annotatedFrame = detectorService.drawDetections(
                        frame, detections
                    )
                else:
                    annotatedFrame = frame

                # 编码为 base64 JPEG
                _, buffer = cv2.imencode(
                    ".jpg", annotatedFrame,
                    [cv2.IMWRITE_JPEG_QUALITY, 70],
                )
                frameBase64 = base64.b64encode(buffer).decode("utf-8")

                # 构造推送消息
                message = {
                    "type": "frame",
                    "frame": frameBase64,
                    "state": {
                        "state": smoothedState,
                        "confidence": round(confidence, 2),
                        "stableDuration": round(
                            timelineService.stableDuration, 1
                        ),
                        "abstractedState": {
                            "isPresent": abstractedState.isPresent,
                            "faceVisible": abstractedState.faceVisible,
                            "headDown": abstractedState.headDown,
                            "headTurnedAway": abstractedState.headTurnedAway,
                            "postureStable": abstractedState.postureStable,
                            "inactiveDuration": round(abstractedState.inactiveDuration, 1),
                            "awayDuration": round(abstractedState.awayDuration, 1),
                            "stableDuration": round(
                                abstractedState.stableDuration, 1
                            ),
                        },
                        "timestamp": time.time(),
                    },
                    "detections": [
                        {
                            "className": d.className,
                            "confidence": d.confidence,
                            "bbox": d.bbox,
                            "keypoints": d.keypoints,
                        }
                        for d in detections
                    ],
                }

                await websocket.send_text(json.dumps(message))

            await asyncio.sleep(pushInterval)

    except WebSocketDisconnect:
        logger.info("WebSocket 客户端断开连接")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
    finally:
        logger.info("WebSocket 会话结束")


# ─── 健康检查 ───
@app.get("/api/health")
async def healthCheck():
    """系统健康检查"""
    return {
        "status": "ok",
        "cameraRunning": cameraService.isRunning,
        "modelLoaded": detectorService.isLoaded,
        "currentState": timelineService.currentState,
    }


@app.get("/api/assets/interruption-audio")
async def getInterruptionAudio():
    """返回分心超过阈值时播放的本地语音文件。"""
    if not INTERRUPTION_AUDIO_PATH.exists():
        raise HTTPException(status_code=404, detail="interrupt.mp3 not found")
    return FileResponse(
        INTERRUPTION_AUDIO_PATH,
        media_type="audio/mpeg",
        filename=INTERRUPTION_AUDIO_PATH.name,
    )


# ─── 直接运行入口 ───
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
    )
