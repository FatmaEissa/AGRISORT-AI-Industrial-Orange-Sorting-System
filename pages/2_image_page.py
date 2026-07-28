"""
pages/2_image_page.py  —  "Image Analysis"
=============================================
Single-image inspection: upload one frame, run detection + classification
once (no tracking/counting — those are video-only concepts), show the
annotated result and a per-detection breakdown.
"""

import numpy as np
import cv2
import streamlit as st

from utils.theming import inject_theme, configure_page
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from backend.loader import load_models
from backend.image_inference import run_image_inference
from config import GRADE_COLOR_MAP

configure_page("Image Analysis")
inject_theme()
render_sidebar()
render_navbar()

st.markdown('<div class="asort-section-title">Image Analysis</div>', unsafe_allow_html=True)

uploaded = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "bmp"])

col_left, col_right = st.columns([2, 1])

if uploaded is not None:
    file_bytes = np.frombuffer(uploaded.getbuffer(), dtype=np.uint8)
    image_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    with col_left:
        with st.status("Loading models…", expanded=False) as status:
            yolo_model, classifier_model, device = load_models()
            status.update(label="Models ready", state="complete")

        with st.spinner("Running detection + classification…"):
            annotated_bgr, detections = run_image_inference(image_bgr, yolo_model, classifier_model, device)

        annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
        st.markdown('<div class="asort-video-frame">', unsafe_allow_html=True)
        st.image(annotated_rgb, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        _, buf = cv2.imencode(".png", annotated_bgr)
        st.download_button(
            "⬇ Download Processed Image", data=buf.tobytes(),
            file_name="processed_" + uploaded.name, mime="image/png",
            use_container_width=True,
        )

    with col_right:
        st.markdown('<div class="asort-section-title">Results</div>', unsafe_allow_html=True)
        if not detections:
            st.info("No oranges detected in this image.")
        else:
            grade_counts = {"A": 0, "B": 0, "C": 0}
            for det in detections:
                grade_counts[det["grade"]] = grade_counts.get(det["grade"], 0) + 1

            cols = st.columns(3)
            for col, grade in zip(cols, ["A", "B", "C"]):
                with col:
                    st.metric(f"Grade {grade}", grade_counts.get(grade, 0))

            st.write("")
            for i, det in enumerate(detections, start=1):
                color = GRADE_COLOR_MAP.get(det["grade"], "#8A9099")
                st.markdown(
                    f"""
                    <div class="asort-info-row">
                        <span class="asort-info-key">Object #{i}</span>
                        <span class="asort-info-value" style="color:{color};">
                            Grade {det['grade']} · {det['classification_conf']*100:.1f}%
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.success(f"{len(detections)} object(s) detected and classified.")
else:
    st.markdown(
        """
        <div class="asort-panel" style="text-align:center;padding:60px 20px;color:var(--text-dim);">
            Upload a JPG or PNG image above to run inspection.
        </div>
        """,
        unsafe_allow_html=True,
    )
