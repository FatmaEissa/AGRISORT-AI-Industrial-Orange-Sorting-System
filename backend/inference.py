"""
backend/inference.py
=====================
This module contains the ORIGINAL AI pipeline logic (YOLO detection,
ByteTrack tracking, ConvNeXt classification, and the final grade decision
algorithm - V4), carried over unchanged from processing.py.

MIGRATION NOTE
--------------
Streamlit has no event loop and no signal/slot system, so the PySide6
`VideoProcessorThread(QThread)` wrapper cannot run as-is. The swap made
here is strictly a transport-layer one:

    Qt version                         Streamlit version
    ---------------------------------  ---------------------------------
    QThread                            threading.Thread (stdlib)
    Signal.emit(...)                   queue.Queue.put(...)
    self._stop_requested flag          threading.Event
    QImage conversion                  raw numpy array (st.image takes
                                        arrays natively, no QImage needed)

Detection thresholds, the tracker config, the classification pipeline,
CLASSIFY_EVERY_N_FRAMES, LAST_N_FRAMES, GRADE_MAP, the counting /
line-crossing logic, and determine_final_grade_v4 are 100% IDENTICAL to
the original script. Nothing about detection, tracking, classification,
or the final grade decision has been changed — only how results are
delivered to the UI layer.
"""

import time
import threading
import queue
from collections import defaultdict

import cv2
import torch
import timm
import torch.nn as nn
import numpy as np
from ultralytics import YOLO
from torchvision import transforms

from config import (
    YOLO_MODEL_PATH, CLASSIFICATION_MODEL_PATH,
    DETECTION_CONF, DETECTION_IOU, DETECTION_IMGSZ, TRACKER_CONFIG,
    CLASSIFY_EVERY_N_FRAMES, LAST_N_FRAMES, GRADE_MAP,
    CLASSIFICATION_MODEL_NAME, CLASSIFICATION_NUM_CLASSES, CLASSIFICATION_DROPOUT,
    IMAGENET_MEAN, IMAGENET_STD,
)


# ==========================================================================
# CLASSIFICATION MODEL (UNCHANGED)
# ==========================================================================
class OrangeClassifier(nn.Module):
    def __init__(self, model_name=CLASSIFICATION_MODEL_NAME,
                 num_classes=CLASSIFICATION_NUM_CLASSES, dropout=CLASSIFICATION_DROPOUT):
        super().__init__()
        self.backbone = timm.create_model(model_name, pretrained=False, num_classes=0, global_pool="avg")
        in_features = self.backbone.num_features
        self.head = nn.Sequential(
            nn.LayerNorm(in_features),
            nn.Dropout(p=dropout),
            nn.Linear(in_features, 512),
            nn.GELU(),
            nn.Dropout(p=dropout * 0.5),
            nn.Linear(512, num_classes)
        )

    def forward(self, x):
        return self.head(self.backbone(x))


def load_classification_model(model_path, device):
    model = OrangeClassifier().to(device)
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    return model


def load_detection_model(model_path):
    return YOLO(model_path)


# ==========================
# TRANSFORMS & CLASSIFICATION (UNCHANGED)
# ==========================
transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
])


def classify_crop(crop, model, device):
    if crop is None or crop.size == 0:
        return None, None, None
    img_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    tensor = transform(img_rgb).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1).squeeze().cpu().numpy()
    pred_idx = int(probs.argmax())
    conf = float(probs[pred_idx])
    return pred_idx, conf, probs


# ==========================
# FINAL DECISION LOGIC (V4) (UNCHANGED)
# ==========================
def determine_final_grade_v4(probs_history):
    if not probs_history:
        return "A"

    recent_probs = probs_history[-LAST_N_FRAMES:]
    avg_probs = np.mean(recent_probs, axis=0)
    avg_A, avg_B, avg_C = avg_probs

    if avg_C >= 0.85:
        return "C"
    elif avg_A >= 0.85:
        return "A"
    else:
        max_avg = max(avg_A, avg_B, avg_C)
        if avg_B == max_avg or max_avg - avg_B <= 0.10:
            return "B"
        else:
            return "A" if avg_A == max_avg else "C"


# ==========================================================================
# STREAMLIT CONNECTION LAYER — threading.Thread + queue.Queue
# (was QThread + Signal in the PySide6 version). No AI logic changed below.
# ==========================================================================
class VideoProcessorWorker:
    """Runs the exact original pipeline on a background thread and pushes
    events onto a thread-safe queue so the Streamlit script (running on
    the main thread) can poll them each rerun and update placeholders.

    Event dicts on the queue look like:
        {"type": "frame", "frame": <np.ndarray RGB>}
        {"type": "stats", "total": int, "a": int, "b": int, "c": int}
        {"type": "fps", "value": float}
        {"type": "frame_index", "current": int, "total": int}
        {"type": "status", "value": str}
        {"type": "device", "value": str}
        {"type": "error", "message": str}
        {"type": "finished"}
    """

    def __init__(self, video_path, save_output=False, event_queue=None):
        self.video_path = video_path
        self.save_output = save_output
        self.queue = event_queue if event_queue is not None else queue.Queue()
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self._thread

    def stop(self):
        self._stop_event.set()

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def _emit(self, event):
        self.queue.put(event)

    def _run(self):
        try:
            self._process()
        except Exception as exc:
            self._emit({"type": "error", "message": str(exc)})
            self._emit({"type": "status", "value": "Stopped"})

    def _process(self):
        # ==========================
        # MAIN PIPELINE (UNCHANGED LOGIC)
        # ==========================
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._emit({"type": "device", "value": "GPU (CUDA)" if device.type == "cuda" else "CPU"})

        self._emit({"type": "status", "value": "Loading YOLO model..."})
        model_yolo = load_detection_model(YOLO_MODEL_PATH)

        self._emit({"type": "status", "value": "Loading classification model..."})
        model_class = load_classification_model(CLASSIFICATION_MODEL_PATH, device)

        video_path = self.video_path
        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        out = None
        if self.save_output:
            out = cv2.VideoWriter(
                "orange_counter_output.mp4",
                cv2.VideoWriter_fourcc(*'mp4v'),
                fps if fps and fps > 0 else 25,
                (width, height)
            )

        line_y = height // 2

        counter_total = 0
        counter_A = 0
        counter_B = 0
        counter_C = 0
        counted_ids = set()
        previous_y = {}
        track_data = defaultdict(lambda: {
            "probs_history": [],
            "last_pred": None,
            "final_grade": None
        })

        results = model_yolo.track(
            source=video_path,
            tracker=TRACKER_CONFIG,
            persist=True,
            stream=True,
            conf=DETECTION_CONF,
            iou=DETECTION_IOU,
            imgsz=DETECTION_IMGSZ,
            verbose=False
        )

        frame_idx = 0
        self._emit({"type": "status", "value": "Running"})
        last_fps_time = time.time()
        fps_frame_counter = 0

        for result in results:
            if self._stop_event.is_set():
                self._emit({"type": "status", "value": "Stopped"})
                break

            frame = result.orig_img
            frame_idx += 1

            cv2.line(frame, (0, line_y), (width, line_y), (0, 255, 255), 3)

            if result.boxes.id is not None:
                boxes = result.boxes.xyxy.cpu().numpy()
                ids = result.boxes.id.cpu().numpy().astype(int)

                for box, track_id in zip(boxes, ids):
                    x1, y1, x2, y2 = map(int, box)
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)

                    if track_id not in previous_y:
                        previous_y[track_id] = cy

                    if frame_idx % CLASSIFY_EVERY_N_FRAMES == 0:
                        crop = frame[y1:y2, x1:x2]
                        if crop.size > 0:
                            pred_idx, conf, probs = classify_crop(crop, model_class, device)
                            if pred_idx is not None:
                                cls_name = GRADE_MAP[pred_idx]
                                track_data[track_id]["last_pred"] = (cls_name, conf)
                                track_data[track_id]["probs_history"].append(probs)

                    last_display = track_data[track_id]["last_pred"]
                    final_grade = track_data[track_id]["final_grade"]
                    label = f"ID:{track_id}"
                    if final_grade is not None:
                        label += f" FINAL:{final_grade}"
                    elif last_display is not None:
                        label += f" {last_display[0]}:{last_display[1]:.2f}"
                    cv2.putText(frame, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

                    if (previous_y[track_id] > line_y >= cy) and (track_id not in counted_ids):
                        probs_history = track_data[track_id]["probs_history"]
                        final_grade = determine_final_grade_v4(probs_history)
                        track_data[track_id]["final_grade"] = final_grade

                        counted_ids.add(track_id)
                        counter_total += 1
                        if final_grade == "A":
                            counter_A += 1
                        elif final_grade == "B":
                            counter_B += 1
                        elif final_grade == "C":
                            counter_C += 1

                        self._emit({"type": "stats", "total": counter_total,
                                     "a": counter_A, "b": counter_B, "c": counter_C})

                    previous_y[track_id] = cy

            cv2.putText(frame, f"TOTAL : {counter_total}", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            cv2.putText(frame, f"GRADE A : {counter_A}", (20, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            cv2.putText(frame, f"GRADE B : {counter_B}", (20, 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
            cv2.putText(frame, f"GRADE C : {counter_C}", (20, 170),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

            if out is not None:
                out.write(frame)

            # ---- Streamlit connection only: push RGB numpy frame to queue ----
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self._emit({"type": "frame", "frame": rgb_frame})
            self._emit({"type": "frame_index", "current": frame_idx, "total": total_frames})

            fps_frame_counter += 1
            now = time.time()
            if now - last_fps_time >= 0.5:
                current_fps = fps_frame_counter / (now - last_fps_time)
                self._emit({"type": "fps", "value": current_fps})
                fps_frame_counter = 0
                last_fps_time = now

        if out is not None:
            out.release()

        if not self._stop_event.is_set():
            self._emit({"type": "status", "value": "Finished"})

        self._emit({"type": "stats", "total": counter_total,
                     "a": counter_A, "b": counter_B, "c": counter_C})
        self._emit({"type": "finished"})
