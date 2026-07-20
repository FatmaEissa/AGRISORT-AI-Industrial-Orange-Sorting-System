# Industrial Orange Sorting System - System Design

## Overview

The Industrial Orange Sorting System is an AI-powered computer vision solution designed to automate the inspection and grading of oranges on industrial production lines. The system performs real-time detection, tracking, classification, grading, and counting through an integrated graphical interface.

---

## Input

- Live camera stream or recorded video
- Continuous frame acquisition
- Real-time processing

---

## Object Detection

Model: **YOLO**

Responsibilities:

- Detect oranges in each frame
- Generate bounding boxes
- Produce confidence scores
- Handle multiple oranges simultaneously

Output:

- Bounding boxes
- Detection confidence

---

## Multi-Object Tracking

Algorithm: **ByteTrack**

Responsibilities:

- Assign a unique ID to every detected orange
- Maintain object identity across frames
- Prevent duplicate counting

Output:

- Stable Track IDs

---

## Image Classification

Model: **ConvNeXt**

Responsibilities:

- Crop each detected orange
- Preprocess the cropped image
- Predict one of three quality classes:

- Grade A
- Grade B
- Grade C

---

## Grade Decision Algorithm

The system stores multiple predictions for every tracked orange.

Instead of relying on a single prediction, the final grade is selected using the average confidence across several frames.

This improves robustness and reduces classification noise.

---

## Counting Module

When an orange crosses the counting line:

- Final grade is confirmed
- Counter is updated
- Statistics are refreshed

---

## Industrial Dashboard

The GUI displays:

- Live video
- Detection boxes
- Track IDs
- Predicted grade
- Orange counters
- Total processed oranges
- Real-time statistics

---

## Technologies

- Python
- OpenCV
- PyTorch
- Ultralytics YOLO
- ByteTrack
- ConvNeXt
- PySide6

---

## Workflow

Video Input

↓

YOLO Detection

↓

ByteTrack Tracking

↓

Orange Cropping

↓

ConvNeXt Classification

↓

Grade Decision

↓

Counting

↓

Industrial Dashboard