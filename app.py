"""
app.py
======
Entry point for the AGRI-SORT Streamlit dashboard.

This is a completely separate application from the existing PySide6
desktop app (main.py + gui.py + processing.py). It reuses the same AI
backend (see backend/inference.py, migrated from processing.py) but is
built for the browser instead of a Qt window.

Run with:
    streamlit run app.py
"""

import streamlit as st

from utils.theming import inject_theme, configure_page
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.metric_cards import render_metric_row
from components.charts import grade_distribution_donut
from config import COLOR_ACCENT, COLOR_SUCCESS, COLOR_INFO_YELLOW, COLOR_DANGER, APP_NAME


def _init_session_state():
    defaults = {
        "processing_status": "Ready",
        "device_str": "—",
        "counter_total": 0,
        "counter_a": 0,
        "counter_b": 0,
        "counter_c": 0,
        "current_fps": 0.0,
        "current_frame": 0,
        "total_frames": 0,
        "worker": None,
        "event_queue": None,
        "history": [],   # list of (timestamp, total) for the timeline chart
        "recent_events": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def main():
    configure_page("Dashboard")
    inject_theme()
    _init_session_state()
    render_sidebar()
    render_navbar()

    st.markdown('<div class="asort-section-title">Overview</div>', unsafe_allow_html=True)

    render_metric_row([
        {"title": "Total Oranges", "value": st.session_state.counter_total, "color": COLOR_ACCENT},
        {"title": "Grade A", "value": st.session_state.counter_a, "color": COLOR_SUCCESS},
        {"title": "Grade B", "value": st.session_state.counter_b, "color": COLOR_INFO_YELLOW},
        {"title": "Grade C", "value": st.session_state.counter_c, "color": COLOR_DANGER},
    ])

    st.write("")
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown('<div class="asort-section-title">Welcome</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="asort-panel">
                <p style="color:var(--text-dim);font-size:13.5px;line-height:1.7;margin:0;">
                    <b style="color:var(--text);">{APP_NAME}</b> is an industrial computer-vision
                    platform for real-time orange quality inspection and sorting.
                    This browser dashboard is a separate front-end that reuses the exact same
                    detection, tracking, and classification pipeline as the desktop control panel.
                </p>
                <br>
                <p style="color:var(--text-dim);font-size:13px;line-height:1.7;margin:0;">
                    Use the sidebar to open <b style="color:var(--accent);">Live Processing</b> for camera / video streams,
                    <b style="color:var(--accent);">Image Analysis</b> for single-frame inspection, or
                    <b style="color:var(--accent);">Statistics</b> to review historical grade distribution.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        st.markdown('<div class="asort-section-title">Grade Split</div>', unsafe_allow_html=True)
        fig = grade_distribution_donut(
            st.session_state.counter_a, st.session_state.counter_b, st.session_state.counter_c
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown(
        f"""
        <div class="asort-statusbar">
            <span>SYSTEM READY</span>
            <span>{APP_NAME} Industrial Inspection Platform</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
