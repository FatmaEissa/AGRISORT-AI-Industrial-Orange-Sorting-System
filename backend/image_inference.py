"""
backend/image_inference.py
============================
Single-image analysis path. Reuses the exact same detection + classification
building blocks as backend/inference.py, run synchronously once (no
threading/queue needed for a single still image).
"""

import cv2
import torch
import numpy as np

from config import (
    DETECTION_CONF, DETECTION_IOU, DETECTION_IMGSZ, GRADE_MAP,
)
from backend.inference import classify_crop


def run_image_inference(image_bgr, model_yolo, model_class, device):
    """
    Runs detection + per-box classification on a single BGR image
    (no tracking, no counting line — those are video-only concepts).

    Returns:
        annotated_bgr: image with boxes/labels drawn
        detections: list of dicts with box, grade, confidence
    """
    frame = image_bgr.copy()
    results = model_yolo.predict(
        source=frame,
        conf=DETECTION_CONF,
        iou=DETECTION_IOU,
        imgsz=DETECTION_IMGSZ,
        verbose=False,
    )

    detections = []
    result = results[0]

    if result.boxes is not None and len(result.boxes) > 0:
        boxes = result.boxes.xyxy.cpu().numpy()
        confs = result.boxes.conf.cpu().numpy()

        for box, det_conf in zip(boxes, confs):
            x1, y1, x2, y2 = map(int, box)
            crop = frame[y1:y2, x1:x2]
            pred_idx, cls_conf, probs = classify_crop(crop, model_class, device)

            grade = GRADE_MAP.get(pred_idx, "?") if pred_idx is not None else "?"

            detections.append({
                "box": (x1, y1, x2, y2),
                "detection_conf": float(det_conf),
                "grade": grade,
                "classification_conf": float(cls_conf) if cls_conf is not None else 0.0,
            })

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{grade} ({cls_conf:.2f})" if cls_conf is not None else "?"
            cv2.putText(frame, label, (x1, max(20, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    return frame, detections
