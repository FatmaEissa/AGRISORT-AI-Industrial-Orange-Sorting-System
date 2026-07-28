"""
pages/1_dashboard.py  —  "Live Processing"
============================================
The core SCADA-style live control panel: upload a video (or point at a
camera index) and watch YOLO + ByteTrack + ConvNeXt run frame-by-frame,
exactly like the desktop app's live view.

THREADING MODEL
----------------
`backend.inference.VideoProcessorWorker` runs the pipeline on a
`threading.Thread` and pushes events onto a `queue.Queue` (see that
file's docstring for the full Qt -> Streamlit mapping).

Streamlit itself is a synchronous script; a plain `while` loop here would
block the whole app and Stop/Start buttons would never register. Instead
the live video area is an `st.fragment(run_every=...)` — only that
fragment re-executes on a timer, draining whatever's currently in the
queue and redrawing the frame/metrics, while the rest of the page (and
its buttons) stays fully interactive between ticks.
"""

import os
import time
import tempfile

import streamlit as st

from utils.theming import inject_theme, configure_page
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.metric_cards import render_metric_row
from components.video_player import render_info_panel, render_status_pill
from utils.formatting import format_frame_progress, safe_pct
from backend.inference import VideoProcessorWorker
from config import COLOR_ACCENT, COLOR_SUCCESS, COLOR_INFO_YELLOW, COLOR_DANGER, STATUS_COLOR_MAP

configure_page("Live Processing")
inject_theme()
render_sidebar()
render_navbar()

st.markdown('<div class="asort-section-title">Live Processing</div>', unsafe_allow_html=True)

# ---- session defaults specific to this page ----
for key, default in {
    "worker": None, "start_time": None, "video_source_name": "--",
    "last_frame": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ==========================================================================
# CONTROLS
# ==========================================================================
ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([2, 1, 1, 1])

with ctrl_col1:
    uploaded = st.file_uploader(
        "Input video", type=["mp4", "avi", "mov", "mkv"], label_visibility="collapsed"
    )

with ctrl_col2:
    save_output = st.checkbox("💾 Save output", value=False)

is_running = st.session_state.worker is not None and st.session_state.worker.is_running()

with ctrl_col3:
    start_clicked = st.button("▶ START", type="primary", use_container_width=True,
                               disabled=is_running or uploaded is None)

with ctrl_col4:
    stop_clicked = st.button("■ STOP", use_container_width=True, disabled=not is_running)

if start_clicked and uploaded is not None:
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, uploaded.name)
    with open(tmp_path, "wb") as f:
        f.write(uploaded.getbuffer())

    st.session_state.video_source_name = uploaded.name
    st.session_state.counter_total = 0
    st.session_state.counter_a = 0
    st.session_state.counter_b = 0
    st.session_state.counter_c = 0
    st.session_state.current_frame = 0
    st.session_state.total_frames = 0
    st.session_state.history = []
    st.session_state.recent_events = []

    worker = VideoProcessorWorker(video_path=tmp_path, save_output=save_output)
    worker.start()
    st.session_state.worker = worker
    st.session_state.start_time = time.time()
    st.session_state.processing_status = "Running"
    st.rerun()

if stop_clicked and st.session_state.worker is not None:
    st.session_state.worker.stop()
    st.toast("Stop requested — finishing current frame…", icon="⏹️")

st.write("")

# ==========================================================================
# TOP METRIC ROW
# ==========================================================================
metric_row_ph = st.empty()

# ==========================================================================
# MAIN BODY: video (70%) + monitoring panel (30%)
# ==========================================================================
video_col, panel_col = st.columns([7, 3])

with video_col:
    st.markdown('<div class="asort-video-frame">', unsafe_allow_html=True)
    video_ph = st.empty()
    progress_ph = st.empty()
    st.markdown('</div>', unsafe_allow_html=True)

with panel_col:
    panel_ph = st.empty()


# ==========================================================================
# LIVE FRAGMENT — polls the queue and redraws every tick without a full
# page rerun, so Start/Stop stay clickable while processing runs.
# ==========================================================================
@st.fragment(run_every=0.15)
def live_render():
    worker = st.session_state.worker
    if worker is None:
        video_ph.markdown(
            '<div style="height:480px;display:flex;align-items:center;justify-content:center;'
            'color:var(--text-dim);font-size:14px;letter-spacing:1px;">NO VIDEO LOADED</div>',
            unsafe_allow_html=True,
        )
        _render_panel()
        _render_metrics()
        return

    # Drain everything currently available without blocking
    drained = 0
    while drained < 200:
        try:
            event = worker.queue.get_nowait()
        except Exception:
            break
        drained += 1
        _handle_event(event)

    if st.session_state.last_frame is not None:
        video_ph.image(st.session_state.last_frame, use_container_width=True)

    pct = safe_pct(st.session_state.current_frame, st.session_state.total_frames)
    progress_ph.progress(pct, text=f"{pct}%")

    _render_panel()
    _render_metrics()


def _handle_event(event):
    etype = event["type"]
    if etype == "frame":
        st.session_state.last_frame = event["frame"]
    elif etype == "stats":
        st.session_state.counter_total = event["total"]
        st.session_state.counter_a = event["a"]
        st.session_state.counter_b = event["b"]
        st.session_state.counter_c = event["c"]
        st.session_state.history.append((time.time() - (st.session_state.start_time or time.time()),
                                          event["total"]))
        st.session_state.recent_events.append(
            f"Counted #{event['total']}  ·  A:{event['a']} B:{event['b']} C:{event['c']}"
        )
        st.session_state.recent_events = st.session_state.recent_events[-8:]
    elif etype == "fps":
        st.session_state.current_fps = event["value"]
    elif etype == "frame_index":
        st.session_state.current_frame = event["current"]
        st.session_state.total_frames = event["total"]
    elif etype == "status":
        st.session_state.processing_status = event["value"]
    elif etype == "device":
        st.session_state.device_str = event["value"]
    elif etype == "error":
        st.session_state.processing_status = "Error"
        st.toast(f"Processing error: {event['message']}", icon="🛑")
    elif etype == "finished":
        pass


def _render_panel():
    with panel_ph.container():
        status = st.session_state.processing_status
        color = STATUS_COLOR_MAP.get(status, "#8A9099")
        render_status_pill(status, color)
        st.write("")
        render_info_panel("System Information", [
            ("Video File", st.session_state.video_source_name),
            ("Tracker", "ByteTrack"),
            ("Current FPS", f"{st.session_state.current_fps:.1f}"),
            ("Current Frame", format_frame_progress(
                st.session_state.current_frame, st.session_state.total_frames)),
            ("Detection Conf.", "0.90"),
            ("Device", st.session_state.device_str),
        ])
        st.write("")
        events_html = "".join(
            f'<div class="asort-info-row"><span class="asort-info-key">•</span>'
            f'<span class="asort-info-value" style="font-weight:500;">{e}</span></div>'
            for e in reversed(st.session_state.recent_events)
        ) or '<div class="asort-info-row"><span class="asort-info-key">No events yet</span></div>'
        st.markdown(
            f'<div class="asort-panel"><div class="asort-panel-title">Recent Events</div>{events_html}</div>',
            unsafe_allow_html=True,
        )


def _render_metrics():
    with metric_row_ph.container():
        render_metric_row([
            {"title": "Total Oranges", "value": st.session_state.counter_total, "color": COLOR_ACCENT},
            {"title": "Grade A", "value": st.session_state.counter_a, "color": COLOR_SUCCESS},
            {"title": "Grade B", "value": st.session_state.counter_b, "color": COLOR_INFO_YELLOW},
            {"title": "Grade C", "value": st.session_state.counter_c, "color": COLOR_DANGER},
            {"title": "FPS", "value": f"{st.session_state.current_fps:.1f}", "color": COLOR_ACCENT},
        ])


live_render()
