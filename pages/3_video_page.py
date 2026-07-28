"""
pages/3_video_page.py  —  "Video Analysis"
=============================================
Batch-style video processing: upload a video, run it end-to-end with a
progress bar (rather than the persistent live monitoring view on the
Dashboard page), then present final counts and let the user download the
annotated output.

Uses the same VideoProcessorWorker thread/queue as Live Processing, but
the fragment here polls to completion rather than staying open for a
continuous camera-style feed.
"""

import os
import time
import tempfile

import streamlit as st

from utils.theming import inject_theme, configure_page
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.metric_cards import render_metric_row
from utils.formatting import safe_pct
from backend.inference import VideoProcessorWorker
from config import COLOR_ACCENT, COLOR_SUCCESS, COLOR_INFO_YELLOW, COLOR_DANGER

configure_page("Video Analysis")
inject_theme()
render_sidebar()
render_navbar()

st.markdown('<div class="asort-section-title">Video Analysis</div>', unsafe_allow_html=True)

for key, default in {"vp_worker": None, "vp_last_frame": None, "vp_done": False}.items():
    if key not in st.session_state:
        st.session_state[key] = default

uploaded = st.file_uploader("Upload a video to process fully", type=["mp4", "avi", "mov", "mkv"], key="vp_uploader")
save_output = st.checkbox("💾 Save processed output for download", value=True, key="vp_save")

run_clicked = st.button("▶ Process Video", type="primary", disabled=uploaded is None)

video_ph = st.empty()
progress_ph = st.empty()
metrics_ph = st.empty()
download_ph = st.empty()

if run_clicked and uploaded is not None:
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, uploaded.name)
    with open(tmp_path, "wb") as f:
        f.write(uploaded.getbuffer())

    st.session_state.counter_total = 0
    st.session_state.counter_a = 0
    st.session_state.counter_b = 0
    st.session_state.counter_c = 0
    st.session_state.vp_done = False

    worker = VideoProcessorWorker(video_path=tmp_path, save_output=save_output)
    worker.start()
    st.session_state.vp_worker = worker
    st.rerun()

worker = st.session_state.vp_worker

if worker is not None and not st.session_state.vp_done:

    @st.fragment(run_every=0.15)
    def process_loop():
        w = st.session_state.vp_worker
        finished = False
        drained = 0
        while drained < 300:
            try:
                event = w.queue.get_nowait()
            except Exception:
                break
            drained += 1
            etype = event["type"]
            if etype == "frame":
                st.session_state.vp_last_frame = event["frame"]
            elif etype == "stats":
                st.session_state.counter_total = event["total"]
                st.session_state.counter_a = event["a"]
                st.session_state.counter_b = event["b"]
                st.session_state.counter_c = event["c"]
            elif etype == "frame_index":
                st.session_state.current_frame = event["current"]
                st.session_state.total_frames = event["total"]
            elif etype == "status":
                st.session_state.processing_status = event["value"]
            elif etype == "error":
                st.toast(f"Error: {event['message']}", icon="🛑")
            elif etype == "finished":
                finished = True

        if st.session_state.vp_last_frame is not None:
            video_ph.image(st.session_state.vp_last_frame, use_container_width=True)

        pct = safe_pct(st.session_state.get("current_frame", 0), st.session_state.get("total_frames", 0))
        progress_ph.progress(pct, text=f"Processing… {pct}%")

        with metrics_ph.container():
            render_metric_row([
                {"title": "Total", "value": st.session_state.counter_total, "color": COLOR_ACCENT},
                {"title": "Grade A", "value": st.session_state.counter_a, "color": COLOR_SUCCESS},
                {"title": "Grade B", "value": st.session_state.counter_b, "color": COLOR_INFO_YELLOW},
                {"title": "Grade C", "value": st.session_state.counter_c, "color": COLOR_DANGER},
            ])

        if finished:
            st.session_state.vp_done = True
            st.rerun()

    process_loop()

elif st.session_state.vp_done:
    st.success("✅ Processing finished.")
    with metrics_ph.container():
        render_metric_row([
            {"title": "Total", "value": st.session_state.counter_total, "color": COLOR_ACCENT},
            {"title": "Grade A", "value": st.session_state.counter_a, "color": COLOR_SUCCESS},
            {"title": "Grade B", "value": st.session_state.counter_b, "color": COLOR_INFO_YELLOW},
            {"title": "Grade C", "value": st.session_state.counter_c, "color": COLOR_DANGER},
        ])
    if st.session_state.vp_last_frame is not None:
        video_ph.image(st.session_state.vp_last_frame, use_container_width=True)

    output_path = "orange_counter_output.mp4"
    if os.path.exists(output_path):
        with open(output_path, "rb") as f:
            download_ph.download_button(
                "⬇ Download Processed Video", data=f.read(),
                file_name="processed_video.mp4", mime="video/mp4",
            )
else:
    video_ph.markdown(
        '<div class="asort-panel" style="text-align:center;padding:60px 20px;color:var(--text-dim);">'
        'Upload a video and click Process Video to begin.</div>',
        unsafe_allow_html=True,
    )
