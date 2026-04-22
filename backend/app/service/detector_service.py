"""
YOLO 目标检测服务

NOTE: 使用 ONNX Runtime 进行本地推理，不依赖 PyTorch。
只检测与学习场景相关的 4 类目标（person, laptop, cell phone, book）。
"""

import logging
from typing import Optional

import cv2
import numpy as np

from app.config import (
    YOLO_MODEL_PATH,
    YOLO_CONFIDENCE_THRESHOLD,
    YOLO_NMS_THRESHOLD,
    YOLO_INPUT_SIZE,
    TARGET_CLASSES,
)
from app.schema.schemas import DetectionItem

logger = logging.getLogger(__name__)


class DetectorService:
    """
    YOLO 检测服务 — 对应概要设计 2.3.1

    负责加载 ONNX 模型并执行推理，输出结构化检测结果。
    """

    def __init__(self) -> None:
        self._session = None
        self._loaded: bool = False

    def loadModel(self) -> bool:
        """
        加载 YOLOv8n ONNX 模型

        Returns:
            是否加载成功
        """
        try:
            import onnxruntime as ort

            self._session = ort.InferenceSession(
                YOLO_MODEL_PATH,
                providers=["CPUExecutionProvider"],
            )
            self._loaded = True
            logger.info(f"YOLO 模型加载成功: {YOLO_MODEL_PATH}")
            return True
        except FileNotFoundError:
            logger.error(
                f"YOLO 模型文件未找到: {YOLO_MODEL_PATH}\n"
                "请下载 yolov8n.onnx 并放到 backend/models/ 目录"
            )
            return False
        except Exception as e:
            logger.error(f"YOLO 模型加载失败: {e}")
            return False

    @property
    def isLoaded(self) -> bool:
        return self._loaded

    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        """
        将 BGR 图像预处理为 YOLO 输入格式

        NOTE: YOLOv8 输入要求 [1, 3, 640, 640]，像素值归一化到 [0, 1]
        """
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (YOLO_INPUT_SIZE, YOLO_INPUT_SIZE))
        img = img.astype(np.float32) / 255.0
        # HWC → CHW → NCHW
        img = np.transpose(img, (2, 0, 1))
        img = np.expand_dims(img, axis=0)
        return img

    def detect(self, frame: np.ndarray) -> list[DetectionItem]:
        """
        执行单帧检测

        Args:
            frame: BGR 格式的原始图像

        Returns:
            检测到的目标列表
        """
        if not self._loaded or self._session is None:
            return []

        h, w = frame.shape[:2]
        inputTensor = self._preprocess(frame)

        # ONNX Runtime 推理
        inputName = self._session.get_inputs()[0].name
        outputs = self._session.run(None, {inputName: inputTensor})

        # YOLO11-pose 输出格式: [1, 56, 8400] → 转置为 [8400, 56]
        # 前 4 列是 cx, cy, w, h；第 5 列是 person 置信度；后 51 列是 17 个关键点 (x,y,conf)
        predictions = outputs[0][0].T

        results: list[DetectionItem] = []

        # 收集所有候选框
        boxes = []
        scores = []
        classIds = []

        for pred in predictions:
            cx, cy, bw, bh = pred[:4]
            confidence = float(pred[4])

            # YOLO pose 只检测 person (classId = 0)
            if confidence < YOLO_CONFIDENCE_THRESHOLD:
                continue

            # 提取 17 个关键点 (x, y, conf)
            # COCO Keypoints: 0:Nose, 1:L-Eye, 2:R-Eye, 3:L-Ear, 4:R-Ear, 5:L-Shoulder, 6:R-Shoulder...
            kpts = pred[5:]
            keypoints = []
            for j in range(17):
                kx = kpts[j * 3] / YOLO_INPUT_SIZE
                ky = kpts[j * 3 + 1] / YOLO_INPUT_SIZE
                kconf = kpts[j * 3 + 2]
                keypoints.append([float(kx), float(ky), float(kconf)])

            # 转换为 x1, y1, x2, y2（归一化坐标）
            x1 = (cx - bw / 2) / YOLO_INPUT_SIZE
            y1 = (cy - bh / 2) / YOLO_INPUT_SIZE
            x2 = (cx + bw / 2) / YOLO_INPUT_SIZE
            y2 = (cy + bh / 2) / YOLO_INPUT_SIZE

            boxes.append([float(x1), float(y1), float(x2 - x1), float(y2 - y1)])
            scores.append(confidence)
            classIds.append(0)
            # HACK: 我们需要保存 NMS 等价的关键点，先把 keypoints 放进一个临时数组，对应每个 box
            if not hasattr(self, "_temp_keypoints"):
                self._temp_keypoints = []
            self._temp_keypoints.append(keypoints)

        # NMS 去重
        if boxes:
            indices = cv2.dnn.NMSBoxes(
                boxes, scores, YOLO_CONFIDENCE_THRESHOLD, YOLO_NMS_THRESHOLD
            )
            if len(indices) > 0:
                for idx in indices.flatten():
                    x, y, bw, bh = boxes[idx]
                    results.append(DetectionItem(
                        className="person",
                        confidence=round(scores[idx], 3),
                        bbox=[
                            round(x, 4),
                            round(y, 4),
                            round(x + bw, 4),
                            round(y + bh, 4),
                        ],
                        keypoints=self._temp_keypoints[idx] if hasattr(self, "_temp_keypoints") else None
                    ))

        if hasattr(self, "_temp_keypoints"):
            self._temp_keypoints.clear()

        return results

    def drawDetections(
        self, frame: np.ndarray, detections: list[DetectionItem]
    ) -> np.ndarray:
        """
        在图像上绘制检测框和标签

        NOTE: 各类别使用不同颜色，便于前端可视化区分
        """
        h, w = frame.shape[:2]
        annotated = frame.copy()

        # 仅 person 类别
        color = (0, 230, 118)

        for det in detections:
            x1 = int(det.bbox[0] * w)
            y1 = int(det.bbox[1] * h)
            x2 = int(det.bbox[2] * w)
            y2 = int(det.bbox[3] * h)

            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            # 绘制置信度
            label = f"person {det.confidence:.2f}"
            labelSize, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - labelSize[1] - 6), (x1 + labelSize[0], y1), color, -1)
            cv2.putText(annotated, label, (x1, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

            # 绘制关键点和骨架
            if det.keypoints:
                # 绘制上半身关键点骨架连线
                skeleton = [
                    (0, 1), (1, 3), (0, 2), (2, 4),  # 头部
                    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10), # 肩膀和手臂
                    (5, 11), (6, 12), (11, 12)  # 躯干
                ]
                
                # 画连线
                for p1, p2 in skeleton:
                    if p1 < len(det.keypoints) and p2 < len(det.keypoints):
                        kp1 = det.keypoints[p1]
                        kp2 = det.keypoints[p2]
                        if kp1[2] > 0.5 and kp2[2] > 0.5:
                            pt1 = (int(kp1[0] * w), int(kp1[1] * h))
                            pt2 = (int(kp2[0] * w), int(kp2[1] * h))
                            cv2.line(annotated, pt1, pt2, (255, 145, 0), 2)
                
                # 画关键点
                for i, kp in enumerate(det.keypoints):
                    if kp[2] > 0.5:
                        px, py = int(kp[0] * w), int(kp[1] * h)
                        # 头部的点用不同颜色
                        pt_color = (0, 0, 255) if i < 5 else (255, 0, 0)
                        cv2.circle(annotated, (px, py), 4, pt_color, -1)

        return annotated


# 全局单例
detectorService = DetectorService()
