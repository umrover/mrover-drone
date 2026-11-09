#!/usr/bin/env python3
import sys
import cv2
import numpy as np

from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QListWidget, QFrame,
                             QGraphicsView, QGraphicsScene, QSizePolicy)
from PyQt6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont, QBrush, QPolygonF
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QPointF

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point

USE_FAKE_STREAM = True
CAMERA_INDEX = 4 # /dev/video4

DARK_THEME = """
QWidget {
    background-color: #07090e;
    color: #94a3b8;
    font-family: 'Consolas', 'Fira Code', 'Roboto Mono', monospace;
    font-size: 12px;
}

QFrame#Panel {
    background-color: #0c1017;
    border: 1px solid #1e293b;
    border-radius: 0px;
}

QPushButton {
    border-radius: 2px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 10px;
    border: 1px solid #334155;
    background-color: #0f172a;
    color: #cbd5e1;
}

QPushButton#CaptureBtn {
    background-color: #032b43;
    border: 1px solid #00f0ff;
    color: #00f0ff;
    font-size: 13px;
}
QPushButton#CaptureBtn:hover { background-color: #00f0ff; color: #000; }

QPushButton#TransmitBtn {
    background-color: #064e3b;
    border: 1px solid #10b981;
    color: #10b981;
    font-size: 13px;
}
QPushButton#TransmitBtn:hover { background-color: #10b981; color: #000; }

QPushButton#ClearBtn:hover { border-color: #ef4444; color: #ef4444; }

QListWidget {
    background-color: #05070a;
    border: 1px solid #1e293b;
    color: #38bdf8;
    font-family: 'Consolas', monospace;
    font-size: 12px;
}

QLabel#TelemetryPill {
    background-color: #02121e;
    border: 1px solid #0284c7;
    color: #38bdf8;
    font-weight: bold;
    padding: 3px 8px;
    font-size: 11px;
}

QLabel#RtkPill {
    background-color: #032014;
    border: 1px solid #10b981;
    color: #10b981;
    font-weight: bold;
    padding: 3px 8px;
    font-size: 11px;
}
"""

# ==============================================================================
# WAYPOINT CANVAS
# ==============================================================================
class WaypointCanvas(QGraphicsView):
    """
    Interactive 2D graphics canvas displaying frozen screenshot.
    Use Qt QGraphicsView scene graph to handle letterboxing, scaling, and aspect ratio.
    """
    point_added = pyqtSignal(float, float)

    def __init__(self):
        super().__init__()
        # QGraphicsScene holds the 2D items
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.pixmap_item = None
        self.points = []

        # disable scrollbars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("border: 1px solid #1e293b; background-color: #03060a;")
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

    def set_frame(self, pixmap):
        """Loads a newly captured aerial frame onto canvas and resets state."""
        self.scene.clear()
        self.points.clear()

        # add captured image as base background item
        self.pixmap_item = self.scene.addPixmap(pixmap)

        # fit scene boundary to image dimensions
        self.setSceneRect(self.pixmap_item.boundingRect())

        # scale view to fit window
        self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

        # draw corner targeting pod brackets on frame
        w, h = pixmap.width(), pixmap.height()
        pen_bracket = QPen(QColor("#00f0ff"), 2)
        bracket_len = 30

        for bx, by, dx, dy in [(15, 15, 1, 1), (w - 15, 15, -1, 1), 
                               (15, h - 15, 1, -1), (w - 15, h - 15, -1, -1)]:
            self.scene.addLine(bx, by, bx + (bracket_len * dx), by, pen_bracket)
            self.scene.addLine(bx, by, bx, by + (bracket_len * dy), pen_bracket)

    def resizeEvent(self, event):
        """Automatically recalculate scale when rescaling window."""
        super().resizeEvent(event)
        if self.pixmap_item:
            # keeps image centered and scaled to window size
            self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

    def mousePressEvent(self, event):
        """Handles mouse clicks on canvas and converts to image pixels."""
        if event.button() == Qt.MouseButton.LeftButton and self.pixmap_item:
            # mapToScene() translates screen window coordinates into unscaled image pixel coordinates
            img_pos = self.mapToScene(event.pos())
            x, y = img_pos.x(), img_pos.y()

            pw = self.pixmap_item.pixmap().width()
            ph = self.pixmap_item.pixmap().height()

            # is waypoint inside image bounds
            if 0 <= x <= pw and 0 <= y <= ph:
                self.points.append((x, y))

                # draw connecting lines
                if len(self.points) > 1:
                    prev_x, prev_y = self.points[-2]
                    pen_line = QPen(QColor("#00f0ff"), 2, Qt.PenStyle.DashLine)
                    self.scene.addLine(prev_x, prev_y, x, y, pen_line)

                # draw diamond marker
                d_size = 10 # diamond radius
                diamond = QPolygonF([QPointF(x, y - d_size), QPointF(x + d_size, y),
                                     QPointF(x, y + d_size), QPointF(x - d_size, y)])
                # amber diamond with translucent fill
                self.scene.addPolygon(diamond, QPen(QColor("#f59e0b"), 2), QBrush(QColor(245, 158, 11, 40)))

                # white micro-crosshair center
                self.scene.addLine(x - 4, y, x + 4, y, QPen(QColor("#ffffff"), 1))
                self.scene.addLine(x, y - 4, x, y + 4, QPen(QColor("#ffffff"), 1))

                # micro tag
                tag = self.scene.addText(f"WP::{len(self.points):02d}", QFont("Consolas", 9, QFont.Weight.Bold))
                tag.setDefaultTextColor(QColor("#f59e0b"))
                tag.setPos(x + 12, y - 10)

                # emit signal to update sidebar UI
                self.point_added.emit(x, y)

    def clear_canvas(self):
        """Clears all drawn markers and lines"""
        if self.pixmap_item:
            self.set_frame(self.pixmap_item.pixmap())

# ==============================================================================
# WINDOW 1: LIVE VTX OPERATOR (MONITOR 1)
# ==============================================================================
class LiveFeedWindow(QWidget):
    """
    Live video stream for primary operator on Monitor 1.
    Renders live VTX stream at 30 fps and provides capture trigger.
    """
    # send raw numpy image array
    frame_captured = pyqtSignal(np.ndarray)

    def __init__(self, cap):
        super().__init__()
        self.cap = cap
        self.setWindowTitle("Monitor 1: Operator Live VTX Feed")
        self.resize(880, 580)

        # telemetry ribbon
        ribbon = QHBoxLayout()
        ribbon.addWidget(QLabel("RECON::NADIR_CAM"))
        ribbon.addStretch()
        p1 = QLabel("LINK::900MHz 99%"); p1.setObjectName("TelemetryPill")
        p2 = QLabel("RTK::FIX [0.02m]"); p2.setObjectName("RtkPill")
        p3 = QLabel("VTX::1.280GHz"); p3.setObjectName("TelemetryPill")
        ribbon.addWidget(p1); ribbon.addWidget(p2); ribbon.addWidget(p3)

        # main video display label
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("border: 1px solid #1e293b; background-color: #03060a;")
        self.video_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.video_label.setMinimumSize(400, 250)

        self.btn_capture = QPushButton("Capture frame // [SPACEBAR]")
        self.btn_capture.setObjectName("CaptureBtn")
        self.btn_capture.setFixedHeight(45)
        self.btn_capture.clicked.connect(self.capture)

        # assemble vertical layout
        layout = QVBoxLayout()
        layout.addLayout(ribbon)
        layout.addWidget(self.video_label, stretch=1)
        layout.addWidget(self.btn_capture)
        self.setLayout(layout)

        self.current_frame = None

        # 30fps refresh timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_feed)
        self.timer.start(33)

    def update_feed(self):
        """Reads frame from camera/video file, draw overlays, and update display."""
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # rewind video
            ret, frame = self.cap.read()
            # guard against read errors or missing files
            if not ret:
                return

        self.current_frame = frame

        # draw HUD reticle on live feed
        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2
        cv2.drawMarker(frame, (cx, cy), (0, 240, 255), cv2.MARKER_CROSS, 40, 1)
        cv2.circle(frame, (cx, cy), 30, (0, 240, 255), 1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        q_img = QImage(rgb.data, w, h, w * 3, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(q_img)

        # render pixmap scaled to label's current size
        self.video_label.setPixmap(pix.scaled(
            self.video_label.width(), self.video_label.height(), 
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def capture(self):
        """Takes a snapshot of current frame and broadcast to Window 2."""
        if self.current_frame is not None:
            self.frame_captured.emit(self.current_frame.copy())

    def keyPressEvent(self, event):
        """Allows operator to press SPACEBAR"""
        if event.key() == Qt.Key.Key_Space:
            self.capture()

# ==============================================================================
# WINDOW 2: WAYPOINT SELECTOR (MONITOR 2)
# ==============================================================================
class WaypointWindow(QWidget):
    def __init__(self, ros_node):
        super().__init__()
        self.ros_node = ros_node
        self.setWindowTitle("Monitor 2: Navigator Waypoint Selector")
        self.resize(1120, 720)

        # Canvas
        self.canvas = WaypointCanvas()
        self.canvas.point_added.connect(self.on_point_added)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Panel")
        sidebar.setFixedWidth(290)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(16, 16, 16, 16)
        side_layout.setSpacing(12)

        title = QLabel("MISSION::TARGETS")
        title.setStyleSheet("font-weight: bold; color: #f8fafc; font-size: 13px;")

        self.status_pill = QLabel("STATUS: STANDBY")
        self.status_pill.setStyleSheet("color: #64748b; font-weight: bold;")

        # list widget showing pixel data for each point
        self.list_widget = QListWidget()

        self.btn_send = QPushButton("Publish // [ENTER]")
        self.btn_send.setObjectName("TransmitBtn")
        self.btn_send.setFixedHeight(45)
        self.btn_send.clicked.connect(self.transmit_waypoints)

        self.btn_clear = QPushButton("Clear Queue // [ESC]")
        self.btn_clear.setObjectName("ClearBtn")
        self.btn_clear.setFixedHeight(36)
        self.btn_clear.clicked.connect(self.clear_all)

        # assemble sidebar
        side_layout.addWidget(title)
        side_layout.addWidget(self.status_pill)
        side_layout.addWidget(QLabel("Staged target data:"))
        side_layout.addWidget(self.list_widget, stretch=1)
        side_layout.addWidget(self.btn_send)
        side_layout.addWidget(self.btn_clear)

        # assemble main window horizontally
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.canvas, stretch=1)
        main_layout.addWidget(sidebar)
        self.setLayout(main_layout)

    def load_frame(self, frame):
        """Slot called whenever operator hits SPACEBAR on Monitor 1."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        q_img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)

        # load pximap onto canvas and reset previous queue
        self.canvas.set_frame(QPixmap.fromImage(q_img))
        self.clear_all()
        self.status_pill.setText("STATUS: AWAITING SELECTIONS")
        self.status_pill.setStyleSheet("color: #00f0ff; font-weight: bold;")

    def on_point_added(self, x, y):
        """Slot called when a new waypoint is clicked on canvas."""
        idx = len(self.canvas.points)
        self.list_widget.addItem(f"[{idx:02d}] :: X:{int(x):04d}  Y:{int(y):04d}")
        self.status_pill.setText(f"STATUS: {idx} TARGETS QUEUED")
        self.status_pill.setStyleSheet("color: #f59e0b; font-weight: bold;")

    def transmit_waypoints(self):
        """Publishes points, called on pressing Enter."""
        if not self.canvas.points:
            self.ros_node.get_logger().warn("Cannot transmit: queue is empty!")
            return

        # Publish each waypoint to /drone/clicked_waypoint
        for idx, (x, y) in enumerate(self.canvas.points):
            msg = Point()
            msg.x = float(x)
            msg.y = float(y)
            msg.z = float(idx + 1)
            self.ros_node.waypoint_pub.publish(msg)
            self.ros_node.get_logger().info(f"Published: WP {idx+1} (X={x:.1f}, Y={y:.1f})")

        # update UI confirmation
        count = len(self.canvas.points)
        self.status_pill.setText(f"Status: {count} WP published")
        self.status_pill.setStyleSheet("color: #10b981; font-weight: bold;")

    def clear_all(self):
        """Clears all staged waypoints from canvas and queue empty."""
        self.canvas.clear_canvas()
        self.list_widget.clear()
        self.status_pill.setText("Queue cleared")
        self.status_pill.setStyleSheet("color: #64748b; font-weight: bold;")

    def keyPressEvent(self, event):
        """Keyboard shortcuts: ENTER to send, ESC to clear."""
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

    # wire capture signal
    win1.frame_captured.connect(win2.load_frame)

    # if 2nd monitor detected, move Window 2 to it and maximize
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
