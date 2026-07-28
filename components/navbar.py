"""
components/navbar.py
=====================
Top navigation bar: logo, project name, system status, device, clock —
mirrors the header bar in the original PySide6 gui.py.
"""

from datetime import datetime
import streamlit as st

from config import APP_NAME, APP_SUBTITLE, COLOR_SUCCESS, COLOR_ACCENT, COLOR_TEXT_DIM


def render_navbar():
    status = st.session_state.get("processing_status", "Ready")
    device = st.session_state.get("device_str", "—")

    status_color = COLOR_SUCCESS if status == "Running" else COLOR_TEXT_DIM
    status_dot_class = "asort-dot pulse" if status == "Running" else "asort-dot"
    device_color = COLOR_SUCCESS if "GPU" in device else COLOR_ACCENT

    now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

    st.markdown(
        f"""
        <div class="asort-navbar">
            <div class="asort-navbar-brand">
                <div class="asort-navbar-logo">AS</div>
                <div>
                    <div class="asort-navbar-title">{APP_NAME} · INDUSTRIAL CONTROL PANEL</div>
                    <div class="asort-navbar-sub">{APP_SUBTITLE}</div>
                </div>
            </div>
            <div class="asort-navbar-metrics">
                <div class="asort-nav-metric">
                    <div class="asort-nav-metric-label">System Status</div>
                    <div class="asort-nav-metric-value">
                        <span class="{status_dot_class}" style="background:{status_color};"></span>{status}
                    </div>
                </div>
                <div class="asort-nav-metric">
                    <div class="asort-nav-metric-label">Device</div>
                    <div class="asort-nav-metric-value">
                        <span class="asort-dot" style="background:{device_color};"></span>{device}
                    </div>
                </div>
                <div class="asort-nav-metric">
                    <div class="asort-nav-metric-label">Date &amp; Time</div>
                    <div class="asort-nav-metric-value">{now_str}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
