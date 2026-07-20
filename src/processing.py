"""
processing.py
==============
This module contains the ORIGINAL AI pipeline logic (YOLO detection,
ByteTrack tracking, ConvNeXt classification, and the final grade decision
algorithm - V4) exactly as provided, fully validated and untouched.

The ONLY changes made to connect it to the PySide6 GUI were:
    - Removed cv2.imshow() / cv2.waitKey() (a live preview window can't be
      used from a background thread - frames are now emitted as Qt signals
      instead so the GUI can display them)
    - Removed the hardcoded video path (now supplied by the GUI's file
      picker) - model paths are unchanged and simply moved to constants
      at the top of the file
    - Wrapped the pipeline inside a QThread with a stop flag and Qt
      signals for frames / counters / FPS / status, since a GUI needs an
      event-driven way to receive this data instead of printing to console
    - Made saving the output video file optional (tied to the "Save
      Output" button in the GUI) instead of always on

Detection thresholds (conf=0.90, iou=0.5, imgsz=640), the tracker config,
the classification pipeline, CLASSIFY_EVERY_N_FRAMES, LAST_N_FRAMES,
GRADE_MAP, the counting/line-crossing logic, and determine_final_grade_v4
are all 100% IDENTICAL to the original script. Nothing about detection,
tracking, classification, or the final grade decision has been changed.
"""

import time
import cv2
import torch
import timm
import torch.nn as nn
import numpy as np
from ultralytics import YOLO
from torchvision import transforms
from collections import defaultdict

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

# ==========================
# CONFIGURATION (UNCHANGED)
# ==========================
CLASSIFY_EVERY_N_FRAMES = 2
GRADE_MAP = {0: "A", 1: "B", 2: "C"}
LAST_N_FRAMES = 7

# Model paths - identical values to the original script, simply hoisted to
# module-level constants so the GUI's "System Information" panel can
# display them. Edit these two lines if your model files move.
YOLO_MODEL_PATH = r"C:\Users\FABRIKA\Documents\Sorting System\best.pt"
CLASSIFICATION_MODEL_PATH = r"C:\Users\FABRIKA\Documents\Sorting System\best_orange_model.pth"


# ==========================
# CLASSIFICATION MODEL (UNCHANGED)
# ==========================
class OrangeClassifier(nn.Module):
    def __init__(self, model_name="convnext_base.fb_in22k_ft_in1k", num_classes=3, dropout=0.35):
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


# ==========================
# TRANSFORMS & CLASSIFICATION (UNCHANGED)
# ==========================
transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
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
# QTHREAD WRAPPER — GUI CONNECTION LAYER ONLY. NO AI LOGIC IS CHANGED BELOW.
# ==========================================================================
class VideoProcessorThread(QThread):
    """Runs the exact original pipeline in a background thread and emits
    Qt signals so the GUI can display live results. This class does not
    alter detection, tracking, classification, or decision logic in any
    way - it only removes the imshow/waitKey preview loop and hardcoded
    video path, replacing them with signal emission and a constructor
    argument, which is the minimum required to run this code behind a GUI
    instead of a blocking OpenCV window."""

    frame_ready = Signal(QImage)
    stats_ready = Signal(int, int, int, int)       # total, A, B, C
    fps_ready = Signal(float)
    frame_index_ready = Signal(int, int)            # current_frame, total_frames
    status_changed = Signal(str)                    # Ready / Running / Stopped / Finished
    device_ready = Signal(str)
    error_occurred = Signal(str)
    finished_processing = Signal()

    def __init__(self, video_path, save_output=False, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.save_output = save_output
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True

    def run(self):
        try:
            self._process()
        except Exception as exc:
            self.error_occurred.emit(str(exc))
            self.status_changed.emit("Stopped")

    def _process(self):
        # ==========================
        # MAIN PIPELINE (UNCHANGED LOGIC)
        # ==========================
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.device_ready.emit("GPU (CUDA)" if device.type == "cuda" else "CPU")

        self.status_changed.emit("Loading YOLO model...")
        model_yolo = YOLO(YOLO_MODEL_PATH)

        self.status_changed.emit("Loading classification model...")
        model_class = load_classification_model(CLASSIFICATION_MODEL_PATH, device)

        video_path = self.video_path
        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()  # Close after extracting properties

        out = None
        if self.save_output:
            out = cv2.VideoWriter(
                "orange_counter_output.mp4",
                cv2.VideoWriter_fourcc(*'mp4v'),
                fps,
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
            tracker="bytetrack.yaml",
            persist=True,
            stream=True,
            conf=0.90,
            iou=0.5,
            imgsz=640,
            verbose=False
        )

        frame_idx = 0
        self.status_changed.emit("Running")
        last_fps_time = time.time()
        fps_frame_counter = 0

        for result in results:
            if self._stop_requested:
                self.status_changed.emit("Stopped")
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

                        self.stats_ready.emit(counter_total, counter_A, counter_B, counter_C)

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

            # ---- GUI connection only: convert BGR frame to QImage & emit ----
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            qimg = QImage(rgb_frame.data, w, h, ch * w, QImage.Format_RGB888).copy()
            self.frame_ready.emit(qimg)
            self.frame_index_ready.emit(frame_idx, total_frames)

            fps_frame_counter += 1
            now = time.time()
            if now - last_fps_time >= 0.5:
                current_fps = fps_frame_counter / (now - last_fps_time)
                self.fps_ready.emit(current_fps)
                fps_frame_counter = 0
                last_fps_time = now

        if out is not None:
            out.release()

        if not self._stop_requested:
            self.status_changed.emit("Finished")

        self.stats_ready.emit(counter_total, counter_A, counter_B, counter_C)
        self.finished_processing.emit()

        # ==========================
        # FINAL STATISTICS (still printed to console, same as original)
        # ==========================
        print("=" * 40)
        print("TOTAL COUNT =", counter_total)
        print("GRADE A =", counter_A)
        print("GRADE B =", counter_B)
        print("GRADE C =", counter_C)
        print("=" * 40)
