"""
utils/theming.py
=================
Injects styles/main.css into the Streamlit app and applies shared page
config. Called once at the top of app.py and every page.
"""

import os
import streamlit as st

_CSS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "styles", "main.css")


def inject_theme():
    with open(_CSS_PATH, "r", encoding="utf-8") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def configure_page(page_title):
    st.set_page_config(
        page_title=f"{page_title} · AGRI-SORT",
        page_icon="🟠",
        layout="wide",
        initial_sidebar_state="expanded",
    )
