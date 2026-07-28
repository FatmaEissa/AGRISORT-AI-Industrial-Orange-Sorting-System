"""
pages/6_about.py  —  "Project Architecture / About"
=======================================================
Static project page: overview, problem/solution, system architecture,
AI pipeline, tech stack, and developer info.
"""

import streamlit as st

from utils.theming import inject_theme, configure_page
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from config import APP_NAME, GITHUB_URL, LINKEDIN_URL

configure_page("Project")
inject_theme()
render_sidebar()
render_navbar()

st.markdown('<div class="asort-section-title">Project Overview</div>', unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="asort-panel">
        <p style="color:var(--text);font-size:14px;line-height:1.8;">
        <b>{APP_NAME}</b> automates fruit and vegetable sorting using computer vision,
        replacing manual visual grading on conveyor lines with a real-time detection,
        tracking, and classification pipeline.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs(["Problem & Solution", "AI Pipeline", "Technologies", "Developer"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            <div class="asort-panel">
                <div class="asort-panel-title">Problem Statement</div>
                <p style="color:var(--text-dim);font-size:13px;line-height:1.8;">
                Manual fruit grading is slow, inconsistent between inspectors, and
                doesn't scale with conveyor throughput in packing facilities.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="asort-panel">
                <div class="asort-panel-title">Solution</div>
                <p style="color:var(--text-dim);font-size:13px;line-height:1.8;">
                A camera-fed computer-vision pipeline detects, tracks, and classifies
                each fruit crossing the conveyor's counting line in real time, assigning
                a quality grade automatically.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

with tab2:
    st.markdown(
        """
        <div class="asort-panel">
            <div class="asort-panel-title">Pipeline Stages</div>
            <div class="asort-info-row"><span class="asort-info-key">1. Detection</span>
                <span class="asort-info-value">YOLOv8 object detection</span></div>
            <div class="asort-info-row"><span class="asort-info-key">2. Tracking</span>
                <span class="asort-info-value">ByteTrack multi-object tracking</span></div>
            <div class="asort-info-row"><span class="asort-info-key">3. Classification</span>
                <span class="asort-info-value">ConvNeXt per-track grading</span></div>
            <div class="asort-info-row"><span class="asort-info-key">4. Decision</span>
                <span class="asort-info-value">Averaged-probability final grade (V4)</span></div>
            <div class="asort-info-row"><span class="asort-info-key">5. Counting</span>
                <span class="asort-info-value">Line-crossing state machine</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with tab3:
    techs = ["Python", "YOLOv8 (Ultralytics)", "ByteTrack", "ConvNeXt", "PyTorch", "timm",
             "OpenCV", "PySide6 (desktop UI)", "Streamlit (web dashboard)", "Plotly"]
    cols = st.columns(5)
    for i, tech in enumerate(techs):
        with cols[i % 5]:
            st.markdown(
                f'<div class="asort-pill" style="margin-bottom:8px;width:100%;justify-content:center;">{tech}</div>',
                unsafe_allow_html=True,
            )

with tab4:
    st.markdown(
        f"""
        <div class="asort-panel">
            <div class="asort-panel-title">Developer</div>
            <p style="color:var(--text-dim);font-size:13px;line-height:1.8;">
            Built as part of the {APP_NAME} project.
            </p>
            <a class="asort-nav-link" href="{GITHUB_URL}" target="_blank">💻 GitHub</a>
            <a class="asort-nav-link" href="{LINKEDIN_URL}" target="_blank">🔗 LinkedIn</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
