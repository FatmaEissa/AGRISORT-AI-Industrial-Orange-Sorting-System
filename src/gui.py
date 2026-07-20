"""
gui.py
=======
Industrial SCADA / HMI style dashboard for the AI Orange Sorting System.

This file contains ONLY presentation / UI code. All AI logic (YOLO
detection, ByteTrack tracking, ConvNeXt classification, and the final
grade decision algorithm) lives untouched in processing.py and is simply
displayed here.
"""

import os
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QPixmap, QFont, QColor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QFileDialog, QProgressBar, QSizePolicy, QSpacerItem,
    QMessageBox
)

from processing import VideoProcessorThread, YOLO_MODEL_PATH, CLASSIFICATION_MODEL_PATH

# ==============================================================================
# COLOR PALETTE
# ==============================================================================
COL_BG = "#15181c"
COL_PANEL = "#1d2126"
COL_CARD = "#20252b"
COL_BORDER = "#2c3138"
COL_BLUE = "#2f9bf0"
COL_ORANGE = "#ff8c1a"
COL_GREEN = "#2ecc71"
COL_YELLOW = "#f1c40f"
COL_RED = "#e74c3c"
COL_TEXT = "#e8eaed"
COL_TEXT_DIM = "#8a9099"

STYLE_SHEET = f"""
QWidget {{
    background-color: {COL_BG};
    color: {COL_TEXT};
    font-family: 'Segoe UI', 'Cairo', Arial, sans-serif;
}}

QFrame#Header {{
    background-color: {COL_PANEL};
    border-bottom: 2px solid {COL_ORANGE};
}}

QFrame#Card {{
    background-color: {COL_CARD};
    border: 1px solid {COL_BORDER};
    border-radius: 10px;
}}

QFrame#VideoFrame {{
    background-color: #0c0e11;
    border: 1px solid {COL_BORDER};
    border-radius: 10px;
}}

QFrame#InfoPanel {{
    background-color: {COL_CARD};
    border: 1px solid {COL_BORDER};
    border-radius: 10px;
}}

QFrame#StatusBar {{
    background-color: {COL_PANEL};
    border-top: 1px solid {COL_BORDER};
}}

QLabel#TitleLabel {{
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 1px;
    color: {COL_TEXT};
}}

QLabel#SubTitleLabel {{
    font-size: 11px;
    color: {COL_TEXT_DIM};
}}

QLabel#CardTitle {{
    font-size: 12px;
    font-weight: 600;
    color: {COL_TEXT_DIM};
    letter-spacing: 1px;
}}

QLabel#CardNumber {{
    font-size: 40px;
    font-weight: 800;
}}

QLabel#InfoKey {{
    font-size: 11px;
    color: {COL_TEXT_DIM};
}}

QLabel#InfoValue {{
    font-size: 12px;
    font-weight: 600;
    color: {COL_TEXT};
}}

QPushButton {{
    background-color: {COL_CARD};
    border: 1px solid {COL_BORDER};
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 12px;
    font-weight: 600;
    color: {COL_TEXT};
}}
QPushButton:hover {{
    background-color: #262b32;
    border: 1px solid {COL_BLUE};
}}
QPushButton:pressed {{
    background-color: #14171b;
}}
QPushButton:disabled {{
    color: {COL_TEXT_DIM};
    border: 1px solid {COL_BORDER};
}}

QPushButton#StartBtn {{
    background-color: {COL_GREEN};
    color: #0c1a10;
    border: none;
}}
QPushButton#StartBtn:hover {{ background-color: #35d67f; }}
QPushButton#StartBtn:disabled {{ background-color: #244430; color: #4d5a51; }}

QPushButton#StopBtn {{
    background-color: {COL_RED};
    color: #250b08;
    border: none;
}}
QPushButton#StopBtn:hover {{ background-color: #ef6455; }}
QPushButton#StopBtn:disabled {{ background-color: #3f2521; color: #6b5450; }}

QPushButton#ExitBtn:hover {{ border: 1px solid {COL_RED}; }}

QPushButton#SaveBtn:checked {{
    border: 1px solid {COL_BLUE};
    color: {COL_BLUE};
}}

QProgressBar {{
    background-color: #0c0e11;
    border: 1px solid {COL_BORDER};
    border-radius: 6px;
    height: 14px;
    text-align: center;
    color: {COL_TEXT};
    font-size: 10px;
}}
QProgressBar::chunk {{
    background-color: {COL_ORANGE};
    border-radius: 6px;
}}
"""


# ==============================================================================
# SMALL REUSABLE WIDGETS
# ==============================================================================
class StatusDot(QLabel):
    """Small colored circle indicator."""

    def __init__(self, color=COL_TEXT_DIM, size=10):
        super().__init__()
        self._size = size
        self.setFixedSize(size, size)
        self.set_color(color)

    def set_color(self, color):
        self.setStyleSheet(
            f"background-color: {color}; border-radius: {self._size // 2}px;"
        )


class DashboardCard(QFrame):
    """A rounded stat card with a title, a big animated number, and an
    accent color bar."""

    def __init__(self, title, accent_color, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.accent_color = accent_color
        self._display_value = 0
        self._target_value = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        accent_bar = QFrame()
        accent_bar.setFixedHeight(4)
        accent_bar.setStyleSheet(
            f"background-color: {accent_color}; border-radius: 2px; border: none;"
        )

        title_label = QLabel(title.upper())
        title_label.setObjectName("CardTitle")

        self.number_label = QLabel("0")
        self.number_label.setObjectName("CardNumber")
        self.number_label.setStyleSheet(f"color: {accent_color};")

        layout.addWidget(accent_bar)
        layout.addWidget(title_label)
        layout.addWidget(self.number_label)
        layout.addStretch()

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate_step)

    def set_value(self, value):
        self._target_value = value
        if not self._anim_timer.isActive():
            self._anim_timer.start(16)

    def _animate_step(self):
        diff = self._target_value - self._display_value
        if diff == 0:
            self._anim_timer.stop()
            return
        step = max(1, abs(diff) // 6)
        self._display_value += step if diff > 0 else -step
        if (diff > 0 and self._display_value > self._target_value) or \
           (diff < 0 and self._display_value < self._target_value):
            self._display_value = self._target_value
        self.number_label.setText(str(self._display_value))


class InfoRow(QWidget):
    """A single key/value row for the System Information panel."""

    def __init__(self, key, value="--"):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 3, 0, 3)
        self.key_label = QLabel(key)
        self.key_label.setObjectName("InfoKey")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("InfoValue")
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.key_label)
        layout.addStretch()
        layout.addWidget(self.value_label)

    def set_value(self, value):
        self.value_label.setText(str(value))


# ==============================================================================
# MAIN WINDOW
# ==============================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Orange Sorting System — Industrial Control Panel")
        self.resize(1440, 860)
        self.setStyleSheet(STYLE_SHEET)

        self.video_path = None
        self.processor_thread = None
        self.start_time = None
        self.total_frames = 0

        self._build_ui()
        self._connect_signals()

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()

        self.elapsed_timer = QTimer(self)
        self.elapsed_timer.timeout.connect(self._update_elapsed)

    # ------------------------------------------------------------------
    # UI CONSTRUCTION
    # ------------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(16, 16, 16, 8)
        body_layout.setSpacing(16)

        body_layout.addWidget(self._build_video_panel(), stretch=3)
        body_layout.addWidget(self._build_dashboard_panel(), stretch=2)

        root.addWidget(body, stretch=1)
        root.addWidget(self._build_status_bar())

    def _build_header(self):
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(74)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 8, 24, 8)

        title_box = QVBoxLayout()
        title = QLabel("AI ORANGE SORTING SYSTEM")
        title.setObjectName("TitleLabel")
        subtitle = QLabel("Industrial Quality Inspection & Sorting Pipeline — YOLOv8 · ByteTrack · ConvNeXt")
        subtitle.setObjectName("SubTitleLabel")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        layout.addLayout(title_box)
        layout.addStretch()

        # System status
        layout.addLayout(self._header_metric("SYSTEM STATUS", "sys_status"))
        layout.addSpacing(28)
        layout.addLayout(self._header_metric("MODEL STATUS", "model_status"))
        layout.addSpacing(28)
        layout.addLayout(self._header_metric("DEVICE", "device"))
        layout.addSpacing(28)
        layout.addLayout(self._header_metric("DATE & TIME", "datetime"))

        return header

    def _header_metric(self, label_text, key):
        box = QVBoxLayout()
        box.setSpacing(2)
        label = QLabel(label_text)
        label.setObjectName("SubTitleLabel")
        row = QHBoxLayout()
        row.setSpacing(6)
        dot = StatusDot(COL_TEXT_DIM)
        value = QLabel("--")
        value.setObjectName("InfoValue")
        row.addWidget(dot)
        row.addWidget(value)
        row_widget = QWidget()
        row_widget.setLayout(row)
        box.addWidget(label)
        box.addWidget(row_widget)

        setattr(self, f"{key}_dot", dot)
        setattr(self, f"{key}_value", value)
        return box

    def _build_video_panel(self):
        container = QVBoxLayout()
        frame = QFrame()
        frame.setObjectName("VideoFrame")
        v = QVBoxLayout(frame)
        v.setContentsMargins(10, 10, 10, 10)

        self.video_label = QLabel("NO VIDEO LOADED")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet(f"color: {COL_TEXT_DIM}; font-size: 14px; border: none;")
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        v.addWidget(self.video_label)

        # progress bar under video
        prog_row = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        prog_row.addWidget(self.progress_bar)
        v.addLayout(prog_row)

        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addWidget(frame)
        wrapper_layout.addLayout(self._build_controls_row())
        return wrapper

    def _build_controls_row(self):
        row = QHBoxLayout()
        row.setSpacing(10)

        self.start_btn = QPushButton("▶  START")
        self.start_btn.setObjectName("StartBtn")

        self.stop_btn = QPushButton("■  STOP")
        self.stop_btn.setObjectName("StopBtn")
        self.stop_btn.setEnabled(False)

        self.save_btn = QPushButton("💾  SAVE OUTPUT")
        self.save_btn.setObjectName("SaveBtn")
        self.save_btn.setCheckable(True)

        self.exit_btn = QPushButton("⏻  EXIT")
        self.exit_btn.setObjectName("ExitBtn")

        row.addWidget(self.start_btn)
        row.addWidget(self.stop_btn)
        row.addWidget(self.save_btn)
        row.addStretch()
        row.addWidget(self.exit_btn)
        return row

    def _build_dashboard_panel(self):
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # --- cards grid ---
        grid = QGridLayout()
        grid.setSpacing(14)

        self.card_total = DashboardCard("Total Count", COL_BLUE)
        self.card_a = DashboardCard("Grade A", COL_GREEN)
        self.card_b = DashboardCard("Grade B", COL_YELLOW)
        self.card_c = DashboardCard("Grade C", COL_RED)

        grid.addWidget(self.card_total, 0, 0, 1, 2)
        grid.addWidget(self.card_a, 1, 0)
        grid.addWidget(self.card_b, 1, 1)
        grid.addWidget(self.card_c, 2, 0, 1, 2)

        layout.addLayout(grid)
        layout.addWidget(self._build_info_panel(), stretch=1)
        return wrapper

    def _build_info_panel(self):
        frame = QFrame()
        frame.setObjectName("InfoPanel")
        v = QVBoxLayout(frame)
        v.setContentsMargins(18, 16, 18, 16)
        v.setSpacing(4)

        title = QLabel("SYSTEM INFORMATION")
        title.setObjectName("CardTitle")
        v.addWidget(title)
        v.addSpacing(6)

        self.info_yolo = InfoRow("YOLO Model", os.path.basename(YOLO_MODEL_PATH))
        self.info_classifier = InfoRow("ConvNeXt Model", os.path.basename(CLASSIFICATION_MODEL_PATH))
        self.info_tracker = InfoRow("Tracker", "ByteTrack")
        self.info_fps = InfoRow("Current FPS", "0.0")
        self.info_processing = InfoRow("Processing Status", "Idle")
        self.info_frame = InfoRow("Current Frame", "0 / 0")
        self.info_video = InfoRow("Video File", "--")
        self.info_elapsed = InfoRow("Elapsed Time", "00:00:00")

        for row in [self.info_yolo, self.info_classifier, self.info_tracker,
                    self.info_fps, self.info_processing, self.info_frame,
                    self.info_video, self.info_elapsed]:
            v.addWidget(row)

        v.addStretch()
        return frame

    def _build_status_bar(self):
        bar = QFrame()
        bar.setObjectName("StatusBar")
        bar.setFixedHeight(36)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 4, 20, 4)

        self.status_dot = StatusDot(COL_TEXT_DIM, size=10)
        self.status_label = QLabel("READY")
        self.status_label.setStyleSheet("font-weight: 700; letter-spacing: 1px;")

        layout.addWidget(self.status_dot)
        layout.addWidget(self.status_label)
        layout.addStretch()

        footer = QLabel("AGRI-SORT Industrial Inspection Platform")
        footer.setObjectName("SubTitleLabel")
        layout.addWidget(footer)
        return bar

    # ------------------------------------------------------------------
    # SIGNALS
    # ------------------------------------------------------------------
    def _connect_signals(self):
        self.start_btn.clicked.connect(self.on_start_clicked)
        self.stop_btn.clicked.connect(self.on_stop_clicked)
        self.exit_btn.clicked.connect(self.close)

    # ------------------------------------------------------------------
    # CLOCK
    # ------------------------------------------------------------------
    def _update_clock(self):
        now = QDateTime.currentDateTime()
        self.datetime_value.setText(now.toString("yyyy-MM-dd  HH:mm:ss"))

    def _update_elapsed(self):
        if self.start_time is None:
            return
        elapsed = datetime.now() - self.start_time
        total_seconds = int(elapsed.total_seconds())
        h, rem = divmod(total_seconds, 3600)
        m, s = divmod(rem, 60)
        self.info_elapsed.set_value(f"{h:02d}:{m:02d}:{s:02d}")

    # ------------------------------------------------------------------
    # CONTROL ACTIONS
    # ------------------------------------------------------------------
    def on_start_clicked(self):
        if self.processor_thread is not None and self.processor_thread.isRunning():
            return

        path, _ = QFileDialog.getOpenFileName(
            self, "Select Input Video", "", "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        if not path:
            return

        self.video_path = path
        self.info_video.set_value(os.path.basename(path))

        self.progress_bar.setValue(0)
        self.card_total.set_value(0)
        self.card_a.set_value(0)
        self.card_b.set_value(0)
        self.card_c.set_value(0)

        self.processor_thread = VideoProcessorThread(
            video_path=path,
            save_output=self.save_btn.isChecked()
        )
        self.processor_thread.frame_ready.connect(self.on_frame_ready)
        self.processor_thread.stats_ready.connect(self.on_stats_ready)
        self.processor_thread.fps_ready.connect(self.on_fps_ready)
        self.processor_thread.frame_index_ready.connect(self.on_frame_index_ready)
        self.processor_thread.status_changed.connect(self.on_status_changed)
        self.processor_thread.device_ready.connect(self.on_device_ready)
        self.processor_thread.error_occurred.connect(self.on_error)
        self.processor_thread.finished_processing.connect(self.on_finished)

        self.start_time = datetime.now()
        self.elapsed_timer.start(1000)

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.save_btn.setEnabled(False)

        self.processor_thread.start()

    def on_stop_clicked(self):
        if self.processor_thread is not None:
            self.processor_thread.stop()
        self.stop_btn.setEnabled(False)

    # ------------------------------------------------------------------
    # SLOTS — receiving data from the processing thread
    # ------------------------------------------------------------------
    def on_frame_ready(self, qimg):
        pixmap = QPixmap.fromImage(qimg)
        scaled = pixmap.scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.video_label.setPixmap(scaled)

    def on_stats_ready(self, total, a, b, c):
        self.card_total.set_value(total)
        self.card_a.set_value(a)
        self.card_b.set_value(b)
        self.card_c.set_value(c)

    def on_fps_ready(self, fps):
        self.info_fps.set_value(f"{fps:.1f}")

    def on_frame_index_ready(self, current, total):
        self.total_frames = total
        self.info_frame.set_value(f"{current} / {total if total else '?'}")
        if total > 0:
            pct = int(min(100, (current / total) * 100))
            self.progress_bar.setValue(pct)

    def on_device_ready(self, device_str):
        self.device_value.setText(device_str)
        self.device_dot.set_color(COL_GREEN if "GPU" in device_str else COL_BLUE)

    def on_status_changed(self, status):
        self.status_label.setText(status.upper())
        self.info_processing.set_value(status)
        self.model_status_value.setText(status)

        color_map = {
            "Ready": COL_TEXT_DIM,
            "Loading YOLO model...": COL_YELLOW,
            "Loading classification model...": COL_YELLOW,
            "Running": COL_GREEN,
            "Stopped": COL_RED,
            "Finished": COL_BLUE,
        }
        color = color_map.get(status, COL_TEXT_DIM)
        self.status_dot.set_color(color)
        self.sys_status_value.setText(status)
        self.sys_status_dot.set_color(color)

        if status in ("Running",):
            self.model_status_dot.set_color(COL_GREEN)
        elif status.startswith("Loading"):
            self.model_status_dot.set_color(COL_YELLOW)

    def on_error(self, message):
        self.elapsed_timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.save_btn.setEnabled(True)
        QMessageBox.critical(self, "Processing Error", message)

    def on_finished(self):
        self.elapsed_timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.save_btn.setEnabled(True)

    # ------------------------------------------------------------------
    def closeEvent(self, event):
        if self.processor_thread is not None and self.processor_thread.isRunning():
            self.processor_thread.stop()
            self.processor_thread.wait(3000)
        event.accept()
