#!/usr/bin/env python3
import sys
import cv2
import numpy as np

from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QListWidget, QFrame,
                             QGraphicsView, QGraphicsScene)
from PyQt6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont, QBrush
from PyQt6.QtCore import QTimer, Qt, pyqtSignal

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point

USE_FAKE_STREAM = True
CAMERA_INDEX = 4 # /dev/video4

DARK_THEME = """
QWidget {
    background-color: #12141a;
    color: #e2e8f0;
    font-family: 'Segoe UI', 'Inter', sans-serif;
}

QFrame#Card {
    background-color: #1a1e29;
    border-radius: 12px;
    border: 1px solid #2d3748;
}

QPushButton {
    border-radius: 8px;
    font-weight: 700;
    font-size: 13px;
    padding: 10px 16px;
    border: none;
}

QPushButton#CaptureBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0ea5e9);
    color: white;
    font-size: 15px;
}
QPushButton#CaptureBtn:hover { background: #0369a1; }

QPushButton#TransmitBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
    color: white;
    font-size: 14px;
}
QPushButton#TransmitBtn:hover { background: #047857; }

QPushButton#ClearBtn {
    background-color: #334155;
    color: #cbd5e1;
}
QPushButton#ClearBtn:hover { background-color: #ef4444; color: white; }

QListWidget {
    background-color: #11141c;
    border: 1px solid #2d3748;
    border-radius: 8px;
    padding: 6px;
    color: #38bdf8;
    font-family: monospace;
    font-size: 13px;
}

QLabel#BadgeLive {
    background-color: #dc2626;
    color: white;
    font-weight: bold;
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 11px;
}

QLabel#BadgeStatus {
    background-color: #0369a1;
    color: white;
    font-weight: bold;
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 11px;
}
"""

class ClickableCanvas(QGraphicsView):
    point_added = pyqtSignal(float, float)

    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.pixmap_item = None
        self.points = []

        # clean display settings
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("border: none; background-color: #0b0f19;")
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

    def set_frame(self, pixmap):
        self.scene.clear()
        self.points.clear()
        self.pixmap_item = self.scene.addPixmap(pixmap)
        self.setSceneRect(self.pixmap_item.boundingRect())
        self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.pixmap_item:
            self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.pixmap_item:
            img_pos = self.mapToScene(event.pos())
            x, y = img_pos.x(), img_pos.y()

            pw = self.pixmap_item.pixmap().width()
            ph = self.pixmap_item.pixmap().height()

            # is waypoint inside image bounds
            if 0 <= x <= pw and 0 <= y <= ph:
                self.points.append((x, y))

                if len(self.points) > 1:
                    prev_x, prev_y = self.points[-2]
                    pen_line = QPen(QColor("#38bdf8"), 2, Qt.PenStyle.DashLine)
                    self.scene.addLine(prev_x, prev_y, x, y, pen_line)

                # Draw outer glow circle
                self.scene.addEllipse(x - 12, y - 12, 24, 24, 
                                      QPen(QColor("#f59e0b"), 2), QBrush(QColor(245, 158, 11, 60)))
                # Draw center pip
                self.scene.addEllipse(x - 3, y - 3, 6, 6, 
                                      QPen(QColor("#f59e0b")), QBrush(QColor("#f59e0b")))

                # Draw number label
                text = self.scene.addText(f"WP {len(self.points)}", QFont("Arial", 10, QFont.Weight.Bold))
                text.setDefaultTextColor(QColor("#ffffff"))
                text.setPos(x + 10, y - 12)

                self.point_added.emit(x, y)

    def clear_canvas(self):
        if self.pixmap_item:
            pix = self.pixmap_item.pixmap()
            self.set_frame(pix)

# window 1: live VTX feed
class LiveFeedWindow(QWidget):
    frame_captured = pyqtSignal(np.ndarray)

    def __init__(self, cap):
        super().__init__()
        self.cap = cap
        self.setWindowTitle("Monitor 1: Operator Live VTX Feed")
        self.resize(850, 560)

        # Top Bar
        top_layout = QHBoxLayout()
        title = QLabel("DOWNWARD VTX STREAM")
        title.setStyleSheet("font-size: 13px; font-weight: bold; color: #94a3b8;")
        badge = QLabel("● LIVE FEED")
        badge.setObjectName("BadgeLive")
        top_layout.addWidget(title)
        top_layout.addStretch()
        top_layout.addWidget(badge)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: #0b0f19; border-radius: 8px;")

        self.btn_capture = QPushButton("Capture Frame [SPACEBAR]")
        self.btn_capture.setObjectName("CaptureBtn")
        self.btn_capture.setFixedHeight(48)
        self.btn_capture.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_capture.clicked.connect(self.capture)

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.video_label, stretch=1)
        layout.addWidget(self.btn_capture)
        self.setLayout(layout)

        self.current_frame = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_feed)
        self.timer.start(33)

    def update_feed(self):
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # rewind video
            ret, frame = self.cap.read()

        if ret:
            self.current_frame = frame
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            q_img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
            pix = QPixmap.fromImage(q_img)
            self.video_label.setPixmap(pix.scaled(
                self.video_label.width(), self.video_label.height(), 
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def capture(self):
        if self.current_frame is not None:
            self.frame_captured.emit(self.current_frame.copy())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.capture()

# window 2: waypoint selector
class WaypointWindow(QWidget):
    def __init__(self, ros_node):
        super().__init__()
        self.ros_node = ros_node
        self.setWindowTitle("Monitor 2: Navigator Waypoint Selector")
        self.resize(1100, 700)

        # Canvas
        self.canvas = ClickableCanvas()
        self.canvas.point_added.connect(self.on_point_added)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(270)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(14, 14, 14, 14)
        side_layout.setSpacing(10)

        side_title = QLabel("MISSION QUEUE")
        side_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #f8fafc;")

        self.status_pill = QLabel("IDLE - NO TARGETS")
        self.status_pill.setObjectName("BadgeStatus")

        self.list_widget = QListWidget()

        self.btn_send = QPushButton("PUBLISH [ENTER]")
        self.btn_send.setObjectName("TransmitBtn")
        self.btn_send.setFixedHeight(48)
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.clicked.connect(self.transmit_waypoints)

        self.btn_clear = QPushButton("Clear Queue [ESC]")
        self.btn_clear.setObjectName("ClearBtn")
        self.btn_clear.setFixedHeight(36)
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_all)

        side_layout.addWidget(side_title)
        side_layout.addWidget(self.status_pill)
        side_layout.addWidget(QLabel("STAGED TARGETS (PIXELS):"))
        side_layout.addWidget(self.list_widget, stretch=1)
        side_layout.addWidget(self.btn_send)
        side_layout.addWidget(self.btn_clear)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.canvas, stretch=1)
        main_layout.addWidget(sidebar)
        self.setLayout(main_layout)

    def load_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        q_img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        self.canvas.set_frame(QPixmap.fromImage(q_img))
        self.clear_all()
        self.status_pill.setText("READY FOR TARGETING")
        self.status_pill.setStyleSheet("background-color: #0284c7; color: white;")

    def on_point_added(self, x, y):
        idx = len(self.canvas.points)
        self.list_widget.addItem(f"WP {idx:02d} ► X:{int(x):04d}    Y:{int(y):04d}")
        self.status_pill.setText(f"{idx} targets queued")
        self.status_pill.setStyleSheet("background-color: #f59e0b; color: black; font-weight: bold;")

    def transmit_waypoints(self):
        """called on pressing Enter"""
        if not self.canvas.points:
            self.ros_node.get_logger().warn("Cannot transmit: queue is empty!")
            return

        for idx, (x, y) in enumerate(self.canvas.points):
            msg = Point()
            msg.x = float(x)
            msg.y = float(y)
            msg.z = float(idx + 1)
            self.ros_node.waypoint_pub.publish(msg)
            self.ros_node.get_logger().info(f"Published: WP {idx+1} (X={x:.1f}, Y={y:.1f})")

        count = len(self.canvas.points)
        self.status_pill.setText(f"✅ {count} WP published")
        self.status_pill.setStyleSheet("background-color: #059669; color: white; font-weight: bold;")

    def clear_all(self):
        self.canvas.clear_canvas()
        self.list_widget.clear()
        self.status_pill.setText("queue cleared")
        self.status_pill.setStyleSheet("background-color: #334155; color: #94a3b8;")

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.transmit_waypoints()
        elif event.key() == Qt.Key.Key_Escape:
            self.clear_all()

def main():
    rclpy.init()
    ros_node = Node("app")
    ros_node.waypoint_pub = ros_node.create_publisher(Point, "/drone/clicked_waypoint", 10)

    if USE_FAKE_STREAM:
        print(f"[INFO] Starting with sample aerial stream...")
        cap = cv2.VideoCapture("sample_footage_1280_720_60fps.mp4")
    else:
        print(f"[INFO] Connecting to /dev/video{CAMERA_INDEX}...")
        # intialize camera
        cap = cv2.VideoCapture(CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)

    # create windows
    win1 = LiveFeedWindow(cap)
    win2 = WaypointWindow(ros_node)

    win1.frame_captured.connect(win2.load_frame)

    screens = app.screens()
    if len(screens) > 1:
        win2.move(screens[1].geometry().topLeft())
        win2.showMaximized()
    else:
        win2.show()
    win1.show()

    ros_timer = QTimer()
    ros_timer.timeout.connect(lambda: rclpy.spin_once(ros_node, timeout_sec=0))
    ros_timer.start(20)

    exit_code = app.exec()

    cap.release()
    ros_node.destroy_node()
    rclpy.shutdown()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

