"""
系统配置管理模块

NOTE: 所有配置项集中管理，避免硬编码分散在各模块中。
敏感信息通过环境变量读取。
"""

import os
from pathlib import Path


# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 数据存储目录
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# 模型文件目录
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)


# ─── 摄像头配置 ───
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
# 采集帧率上限，降低 CPU 占用
CAMERA_FPS = int(os.getenv("CAMERA_FPS", "15"))
CAMERA_WIDTH = int(os.getenv("CAMERA_WIDTH", "640"))
CAMERA_HEIGHT = int(os.getenv("CAMERA_HEIGHT", "480"))


# ─── YOLO 检测配置 ───
YOLO_MODEL_PATH = str(MODELS_DIR / "yolo11n-pose.onnx")
YOLO_CONFIDENCE_THRESHOLD = float(os.getenv("YOLO_CONFIDENCE", "0.5"))
YOLO_NMS_THRESHOLD = float(os.getenv("YOLO_NMS", "0.45"))
YOLO_INPUT_SIZE = 640

# COCO 数据集中我们关注的目标类别及其 ID
# NOTE: YOLO pose 模型只输出 person 类别（0）
TARGET_CLASSES = {
    0: "person",
}


# ─── 规则引擎配置 ───
# 滑动窗口大小（帧数），用于时间序列平滑
SLIDING_WINDOW_SIZE = int(os.getenv("SLIDING_WINDOW_SIZE", "30"))
# 状态切换的最小持续帧数阈值，低于此值不切换状态
STATE_CHANGE_THRESHOLD = int(os.getenv("STATE_CHANGE_THRESHOLD", "10"))


# ─── 数据库配置 ───
DATABASE_URL = f"sqlite:///{DATA_DIR / 'study_monitor.db'}"


# ─── 服务端配置 ───
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# ─── Ollama 配置 ───
# Use 127.0.0.1 and disable env proxies in the client so local model calls are
# not routed through system HTTP_PROXY/ALL_PROXY settings.
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "qwen2.5:1.5b")

# WebSocket 推送间隔（毫秒）
WS_PUSH_INTERVAL_MS = int(os.getenv("WS_PUSH_INTERVAL_MS", "66"))  # ~15fps
