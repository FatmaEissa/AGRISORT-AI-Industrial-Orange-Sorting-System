"""
components/charts.py
=====================
Plotly chart builders, pre-styled for the dark industrial theme.
"""

import plotly.graph_objects as go
from config import (
    COLOR_CARD, COLOR_BORDER, COLOR_TEXT, COLOR_TEXT_DIM,
    COLOR_SUCCESS, COLOR_INFO_YELLOW, COLOR_DANGER, COLOR_ACCENT,
)

_LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=COLOR_TEXT, family="Inter, sans-serif", size=12),
    margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)


def grade_distribution_donut(a, b, c):
    values = [a, b, c]
    labels = ["Grade A", "Grade B", "Grade C"]
    colors = [COLOR_SUCCESS, COLOR_INFO_YELLOW, COLOR_DANGER]

    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=0.62,
        marker=dict(colors=colors, line=dict(color=COLOR_CARD, width=3)),
        textinfo="label+percent", textfont=dict(color=COLOR_TEXT, size=12),
    )])
    total = a + b + c
    fig.update_layout(
        **_LAYOUT_BASE,
        showlegend=False,
        annotations=[dict(text=f"{total}<br><span style='font-size:11px;color:{COLOR_TEXT_DIM}'>TOTAL</span>",
                           x=0.5, y=0.5, font=dict(size=26, color=COLOR_TEXT), showarrow=False)],
        height=280,
    )
    return fig


def processing_timeline(timestamps, totals):
    fig = go.Figure(data=[go.Scatter(
        x=timestamps, y=totals, mode="lines", fill="tozeroy",
        line=dict(color=COLOR_ACCENT, width=2.5),
        fillcolor="rgba(47,155,240,0.12)",
    )])
    fig.update_layout(
        **_LAYOUT_BASE,
        xaxis=dict(showgrid=False, color=COLOR_TEXT_DIM),
        yaxis=dict(showgrid=True, gridcolor=COLOR_BORDER, color=COLOR_TEXT_DIM),
        height=260,
    )
    return fig


def grade_bar_chart(a, b, c):
    fig = go.Figure(data=[go.Bar(
        x=["Grade A", "Grade B", "Grade C"], y=[a, b, c],
        marker_color=[COLOR_SUCCESS, COLOR_INFO_YELLOW, COLOR_DANGER],
        marker_line_width=0,
        text=[a, b, c], textposition="outside",
    )])
    fig.update_layout(
        **_LAYOUT_BASE,
        xaxis=dict(showgrid=False, color=COLOR_TEXT_DIM),
        yaxis=dict(showgrid=True, gridcolor=COLOR_BORDER, color=COLOR_TEXT_DIM),
        height=280,
    )
    return fig
