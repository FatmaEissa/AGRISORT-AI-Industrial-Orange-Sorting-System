"""
pages/4_statistics.py  —  "Statistics"
=========================================
Aggregated analytics for the current session: grade distribution,
processing timeline (count over time), and recent detection history.
"""

import streamlit as st

from utils.theming import inject_theme, configure_page
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.charts import grade_distribution_donut, processing_timeline, grade_bar_chart
from components.metric_cards import render_metric_row
from config import COLOR_ACCENT, COLOR_SUCCESS, COLOR_INFO_YELLOW, COLOR_DANGER

configure_page("Statistics")
inject_theme()
render_sidebar()
render_navbar()

st.markdown('<div class="asort-section-title">Statistics</div>', unsafe_allow_html=True)

total = st.session_state.get("counter_total", 0)
a = st.session_state.get("counter_a", 0)
b = st.session_state.get("counter_b", 0)
c = st.session_state.get("counter_c", 0)
history = st.session_state.get("history", [])

if total == 0:
    st.markdown(
        '<div class="asort-panel" style="text-align:center;padding:60px 20px;color:var(--text-dim);">'
        'No processing data yet. Run Live Processing or Video Analysis to generate statistics.</div>',
        unsafe_allow_html=True,
    )
else:
    render_metric_row([
        {"title": "Total Processed", "value": total, "color": COLOR_ACCENT},
        {"title": "Grade A", "value": a, "color": COLOR_SUCCESS, "footer": f"{a/total*100:.1f}%"},
        {"title": "Grade B", "value": b, "color": COLOR_INFO_YELLOW, "footer": f"{b/total*100:.1f}%"},
        {"title": "Grade C", "value": c, "color": COLOR_DANGER, "footer": f"{c/total*100:.1f}%"},
    ])

    st.write("")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="asort-section-title">Grade Distribution</div>', unsafe_allow_html=True)
        st.plotly_chart(grade_distribution_donut(a, b, c), use_container_width=True,
                         config={"displayModeBar": False})
    with col2:
        st.markdown('<div class="asort-section-title">Grade Comparison</div>', unsafe_allow_html=True)
        st.plotly_chart(grade_bar_chart(a, b, c), use_container_width=True,
                         config={"displayModeBar": False})

    if history:
        st.markdown('<div class="asort-section-title">Processing Timeline</div>', unsafe_allow_html=True)
        timestamps = [h[0] for h in history]
        totals = [h[1] for h in history]
        st.plotly_chart(processing_timeline(timestamps, totals), use_container_width=True,
                         config={"displayModeBar": False})

    events = st.session_state.get("recent_events", [])
    if events:
        st.markdown('<div class="asort-section-title">Recent Detection History</div>', unsafe_allow_html=True)
        events_html = "".join(
            f'<div class="asort-info-row"><span class="asort-info-key">•</span>'
            f'<span class="asort-info-value" style="font-weight:500;">{e}</span></div>'
            for e in reversed(events)
        )
        st.markdown(f'<div class="asort-panel">{events_html}</div>', unsafe_allow_html=True)
