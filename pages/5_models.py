"""
pages/5_models.py  —  "Models"
=================================
Read-only model information page: architectures, thresholds, tracker
config, class labels, and model file paths.
"""

import os
import torch
import streamlit as st

from utils.theming import inject_theme, configure_page
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.video_player import render_info_panel
from config import (
    YOLO_MODEL_PATH, CLASSIFICATION_MODEL_PATH, DETECTION_CONF, DETECTION_IOU,
    DETECTION_IMGSZ, TRACKER_CONFIG, CLASSIFICATION_MODEL_NAME,
    CLASSIFICATION_INPUT_SIZE, GRADE_LABELS,
)

configure_page("Models")
inject_theme()
render_sidebar()
render_navbar()

st.markdown('<div class="asort-section-title">Model Information</div>', unsafe_allow_html=True)

device = "GPU (CUDA)" if torch.cuda.is_available() else "CPU"

col1, col2 = st.columns(2)

with col1:
    render_info_panel("Detection Model — YOLO", [
        ("Version", "YOLOv8"),
        ("Model File", os.path.basename(YOLO_MODEL_PATH)),
        ("Model Path", YOLO_MODEL_PATH),
        ("Input Size", f"{DETECTION_IMGSZ} × {DETECTION_IMGSZ}"),
        ("Confidence Threshold", f"{DETECTION_CONF:.2f}"),
        ("IoU Threshold", f"{DETECTION_IOU:.2f}"),
        ("Tracker", TRACKER_CONFIG),
    ])

with col2:
    render_info_panel("Classification Model — ConvNeXt", [
        ("Architecture", CLASSIFICATION_MODEL_NAME),
        ("Model File", os.path.basename(CLASSIFICATION_MODEL_PATH)),
        ("Model Path", CLASSIFICATION_MODEL_PATH),
        ("Input Size", f"{CLASSIFICATION_INPUT_SIZE} × {CLASSIFICATION_INPUT_SIZE}"),
        ("Classes", ", ".join(f"Grade {g}" for g in GRADE_LABELS)),
        ("Current Device", device),
    ])

st.write("")
st.markdown(
    """
    <div class="asort-panel">
        <div class="asort-panel-title">Pipeline Notes</div>
        <p style="color:var(--text-dim);font-size:12.5px;line-height:1.7;">
        Classification runs every 2nd frame per tracked object. The final grade for each
        object is decided once it crosses the counting line, using an averaged-probability
        rule over the last 7 classified frames (favoring Grade B on close calls, and
        requiring ≥0.85 average confidence to commit directly to Grade A or C).
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
