"""
main.py
========
Entry point for the AI Orange Sorting System industrial GUI.

Run with:
    python main.py

Requirements:
    pip install PySide6 opencv-python torch timm torchvision ultralytics numpy

The AI pipeline (YOLO + ByteTrack + ConvNeXt + decision logic) lives
untouched in processing.py. This file only starts the Qt application and
shows the dashboard defined in gui.py.
"""

import sys
from PySide6.QtWidgets import QApplication
from gui import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
