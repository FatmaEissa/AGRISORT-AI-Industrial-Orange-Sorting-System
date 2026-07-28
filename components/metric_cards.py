"""
components/metric_cards.py
============================
Renders the large professional KPI cards (Total, Grade A/B/C, FPS, etc.)
seen across the dashboard.
"""

import streamlit as st
from config import COLOR_ACCENT


def render_metric_card(title, value, accent_color=COLOR_ACCENT, footer=None):
    footer_html = f'<div class="asort-card-footer">{footer}</div>' if footer else ""
    st.markdown(
        f"""
        <div class="asort-card" style="--accent-bar: {accent_color};">
            <div class="asort-card-title">{title}</div>
            <div class="asort-card-value" style="color:{accent_color};">{value}</div>
            {footer_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_row(cards):
    """cards: list of dicts with keys title, value, color, footer(optional)"""
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            render_metric_card(
                card["title"], card["value"],
                card.get("color", COLOR_ACCENT), card.get("footer"),
            )
