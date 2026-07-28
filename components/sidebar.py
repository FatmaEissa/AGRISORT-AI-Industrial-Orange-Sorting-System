"""
components/sidebar.py
======================
Sidebar navigation: page links + documentation / GitHub / LinkedIn.
"""

import streamlit as st
from config import APP_NAME, GITHUB_URL, LINKEDIN_URL


def render_sidebar():
    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding:4px 10px 18px 10px;">
                <div style="font-size:15px;font-weight:800;letter-spacing:0.5px;">
                    🟠 {APP_NAME}
                </div>
                <div style="font-size:10.5px;color:#8A9099;">Industrial Inspection Platform</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.page_link("app.py", label="Dashboard", icon="📊")
        st.page_link("pages/1_dashboard.py", label="Live Processing", icon="🎥")
        st.page_link("pages/2_image_page.py", label="Image Analysis", icon="🖼️")
        st.page_link("pages/3_video_page.py", label="Video Analysis", icon="🎞️")
        st.page_link("pages/4_statistics.py", label="Statistics", icon="📈")
        st.page_link("pages/5_models.py", label="Models", icon="🧠")
        st.page_link("pages/6_about.py", label="Project Architecture", icon="🏗️")

        st.markdown("<hr style='margin:14px 0;'>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <a class="asort-nav-link" href="https://docs.streamlit.io" target="_blank">📄 Documentation</a>
            <a class="asort-nav-link" href="{GITHUB_URL}" target="_blank">💻 GitHub</a>
            <a class="asort-nav-link" href="{LINKEDIN_URL}" target="_blank">🔗 LinkedIn</a>
            """,
            unsafe_allow_html=True,
        )
