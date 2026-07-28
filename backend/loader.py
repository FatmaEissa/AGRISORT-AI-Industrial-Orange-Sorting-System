"""
backend/loader.py
==================
Model loading with Streamlit's resource cache so YOLO / ConvNeXt weights
are loaded once per session instead of on every script rerun (Streamlit
reruns the whole script on every interaction, so this cache is essential
for responsiveness).
"""

import streamlit as st
import torch

from config import YOLO_MODEL_PATH, CLASSIFICATION_MODEL_PATH
from backend.inference import load_detection_model, load_classification_model


def get_device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


@st.cache_resource(show_spinner=False)
def load_models():
    """Loads and caches both models. Returns (yolo_model, classifier_model, device)."""
    device = get_device()
    yolo_model = load_detection_model(YOLO_MODEL_PATH)
    classifier_model = load_classification_model(CLASSIFICATION_MODEL_PATH, device)
    return yolo_model, classifier_model, device
