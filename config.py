"""
config.py
=========
Single source of truth for paths, AI pipeline thresholds, and theme tokens.

Nothing about the AI pipeline's behavior changes by editing this file's
values (they mirror processing.py's original constants) — this just makes
them importable/relative instead of hardcoded absolute Windows paths.
"""

import os

# ==========================================================================
# PATHS (relative — required for Streamlit Community Cloud deployment)
# ==========================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

YOLO_MODEL_PATH = os.path.join(BASE_DIR, "models", "detection", "best.pt")
CLASSIFICATION_MODEL_PATH = os.path.join(
    BASE_DIR, "models", "classification", "best_orange_model.pth"
)

# ==========================================================================
# AI PIPELINE CONSTANTS — IDENTICAL to the original processing.py
# ==========================================================================
DETECTION_CONF = 0.90
DETECTION_IOU = 0.5
DETECTION_IMGSZ = 640
TRACKER_CONFIG = "bytetrack.yaml"

CLASSIFY_EVERY_N_FRAMES = 2
LAST_N_FRAMES = 7
GRADE_MAP = {0: "A", 1: "B", 2: "C"}
GRADE_LABELS = ["A", "B", "C"]

CLASSIFICATION_MODEL_NAME = "convnext_base.fb_in22k_ft_in1k"
CLASSIFICATION_INPUT_SIZE = 224
CLASSIFICATION_NUM_CLASSES = 3
CLASSIFICATION_DROPOUT = 0.35

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# ==========================================================================
# APP METADATA
# ==========================================================================
APP_NAME = "AGRI-SORT"
APP_SUBTITLE = "Industrial Orange Quality Inspection & Sorting Platform"
APP_TAGLINE = "YOLOv8 · ByteTrack · ConvNeXt"

GITHUB_URL = "https://github.com/"
LINKEDIN_URL = "https://linkedin.com/"

# ==========================================================================
# THEME — Dark Industrial (SCADA-style)
# ==========================================================================
COLOR_BG = "#0E1117"
COLOR_CARD = "#1C1F26"
COLOR_BORDER = "#2E3440"
COLOR_PANEL = "#161920"

COLOR_ACCENT = "#2F9BF0"      # Industrial Blue
COLOR_SUCCESS = "#2ECC71"     # Green
COLOR_WARNING = "#FF8C1A"     # Orange
COLOR_DANGER = "#E74C3C"      # Red
COLOR_INFO_YELLOW = "#F1C40F"

COLOR_TEXT = "#E8EAED"
COLOR_TEXT_DIM = "#8A9099"

FONT_STACK = "'Inter', 'Roboto', 'IBM Plex Sans', -apple-system, sans-serif"

GRADE_COLOR_MAP = {
    "A": COLOR_SUCCESS,
    "B": COLOR_INFO_YELLOW,
    "C": COLOR_DANGER,
}

STATUS_COLOR_MAP = {
    "Ready": COLOR_TEXT_DIM,
    "Idle": COLOR_TEXT_DIM,
    "Loading YOLO model...": COLOR_WARNING,
    "Loading classification model...": COLOR_WARNING,
    "Running": COLOR_SUCCESS,
    "Stopped": COLOR_DANGER,
    "Finished": COLOR_ACCENT,
    "Error": COLOR_DANGER,
}
