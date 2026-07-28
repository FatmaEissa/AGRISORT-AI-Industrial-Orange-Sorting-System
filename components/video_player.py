"""
components/video_player.py
============================
Renders the live/processed video area and the right-hand monitoring
info panel (mirrors the "InfoRow" list in the original gui.py).
"""

import streamlit as st


def render_info_panel(title, rows):
    """rows: list of (key, value) tuples"""
    rows_html = "".join(
        f'<div class="asort-info-row"><span class="asort-info-key">{k}</span>'
        f'<span class="asort-info-value">{v}</span></div>'
        for k, v in rows
    )
    st.markdown(
        f"""
        <div class="asort-panel">
            <div class="asort-panel-title">{title}</div>
            {rows_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_pill(label, color):
    st.markdown(
        f'<span class="asort-pill" style="color:{color};border-color:{color}66;">'
        f'<span class="asort-dot" style="background:{color};"></span>{label}</span>',
        unsafe_allow_html=True,
    )
