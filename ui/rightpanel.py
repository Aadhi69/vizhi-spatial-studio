from PyQt6.QtWidgets import QFrame, QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QPushButton, QProgressBar
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor
from ui.viewport import create_vector_icon

class RightPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RightPanel")
        
        # Scroll area for high-DPI resolution safety
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        pipe_title = QLabel("Capture & Pipeline")
        pipe_title.setObjectName("SectionTitle")
        layout.addWidget(pipe_title)

        # RTSP Stream URL input field
        rtsp_header_layout = QHBoxLayout()
        rtsp_header_layout.setSpacing(4)
        rtsp_header_layout.setContentsMargins(0, 0, 0, 0)
        self.rtsp_dot = QLabel("●")
        self.rtsp_dot.setStyleSheet("color: #6F7682; font-size: 10px; background: transparent; border: none; padding-bottom: 1px;")
        rtsp_lbl = QLabel("RTSP Stream")
        rtsp_lbl.setStyleSheet("font-size: 10px; font-weight: bold; color: #6F7682; letter-spacing: 1.2px; text-transform: uppercase; background: transparent;")
        rtsp_header_layout.addWidget(self.rtsp_dot)
        rtsp_header_layout.addWidget(rtsp_lbl)
        rtsp_header_layout.addStretch()
        layout.addLayout(rtsp_header_layout)

        self.rtsp_input = QLineEdit("rtsp://127.0.0.1:8554/live")
        self.rtsp_input.setObjectName("RtspInput")
        
        # Inner checkmark label layout
        rtsp_inner_layout = QHBoxLayout(self.rtsp_input)
        rtsp_inner_layout.setContentsMargins(0, 0, 10, 0)
        self.connected_indicator = QLabel("Connected")
        self.connected_indicator.setStyleSheet("color: #58C777; font-size: 11px; font-weight: bold; background: transparent;")
        rtsp_inner_layout.addStretch()
        rtsp_inner_layout.addWidget(self.connected_indicator)
        
        layout.addWidget(self.rtsp_input)

        # Frame save frequency
        save_every_lbl_r = QLabel("Save Every N Frames")
        save_every_lbl_r.setStyleSheet("font-size: 10px; font-weight: bold; color: #6F7682; letter-spacing: 1.2px; text-transform: uppercase;")
        layout.addWidget(save_every_lbl_r)

        self.right_frame_spin = QSpinBox()
        self.right_frame_spin.setValue(5)
        self.right_frame_spin.setRange(1, 100)
        layout.addWidget(self.right_frame_spin)

        layout.addSpacing(6)

        # Workstation Action buttons
        self.restart_btn = QPushButton("  Restart RTSP")
        self.restart_btn.setIcon(create_vector_icon("refresh", QColor("#cbd5e1")))
        
        self.start_btn = QPushButton("  Start Capture")
        self.start_btn.setObjectName("PrimaryButton")
        self.start_btn.setIcon(create_vector_icon("play", QColor("#ffffff")))
        
        self.stop_btn = QPushButton("  Stop Capture")
        self.stop_btn.setIcon(create_vector_icon("stop", QColor("#cbd5e1")))
        
        self.colmap_btn = QPushButton("  Run COLMAP")
        self.colmap_btn.setIcon(create_vector_icon("reconstruction", QColor("#cbd5e1")))
        
        self.gaussian_btn = QPushButton("  Train Gaussian")
        self.gaussian_btn.setIcon(create_vector_icon("gaussian", QColor("#cbd5e1")))
        
        self.cancel_btn = QPushButton("  Cancel Task")
        self.cancel_btn.setObjectName("CancelButton")
        self.cancel_btn.setIcon(create_vector_icon("cancel", QColor("#fca5a5")))

        for btn in [self.restart_btn, self.start_btn, self.stop_btn, self.colmap_btn, self.gaussian_btn, self.cancel_btn]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(btn)

        layout.addSpacing(10)

        # Pipeline progress indicators
        progress_title = QLabel("Task Progress")
        progress_title.setObjectName("SectionTitle")
        layout.addWidget(progress_title)

        # COLMAP
        colmap_header_layout = QHBoxLayout()
        colmap_header_layout.setSpacing(4)
        colmap_header_layout.setContentsMargins(0, 0, 0, 0)
        self.colmap_dot = QLabel("●")
        self.colmap_dot.setStyleSheet("color: #6F7682; font-size: 10px; background: transparent; border: none; padding-bottom: 1px;")
        self.colmap_lbl = QLabel("COLMAP: Idle")
        self.colmap_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #6F7682; background: transparent;")
        colmap_header_layout.addWidget(self.colmap_dot)
        colmap_header_layout.addWidget(self.colmap_lbl)
        colmap_header_layout.addStretch()
        layout.addLayout(colmap_header_layout)

        colmap_prog_layout = QHBoxLayout()
        self.colmap_progress = QProgressBar()
        self.colmap_progress.setValue(0)
        self.colmap_progress.setTextVisible(False)
        colmap_prog_layout.addWidget(self.colmap_progress)
        
        self.colmap_pct = QLabel("Idle")
        self.colmap_pct.setStyleSheet("font-size: 11px; font-weight: bold; color: #6F7682; min-width: 45px;")
        self.colmap_pct.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        colmap_prog_layout.addWidget(self.colmap_pct)
        layout.addLayout(colmap_prog_layout)

        # Gaussian
        gaussian_header_layout = QHBoxLayout()
        gaussian_header_layout.setSpacing(4)
        gaussian_header_layout.setContentsMargins(0, 0, 0, 0)
        self.gaussian_dot = QLabel("●")
        self.gaussian_dot.setStyleSheet("color: #6F7682; font-size: 10px; background: transparent; border: none; padding-bottom: 1px;")
        self.gaussian_lbl = QLabel("Gaussian: Idle")
        self.gaussian_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #6F7682; background: transparent;")
        gaussian_header_layout.addWidget(self.gaussian_dot)
        gaussian_header_layout.addWidget(self.gaussian_lbl)
        gaussian_header_layout.addStretch()
        layout.addLayout(gaussian_header_layout)

        gaussian_prog_layout = QHBoxLayout()
        self.gaussian_progress = QProgressBar()
        self.gaussian_progress.setValue(0)
        self.gaussian_progress.setTextVisible(False)
        gaussian_prog_layout.addWidget(self.gaussian_progress)
        
        self.gaussian_pct = QLabel("Idle")
        self.gaussian_pct.setStyleSheet("font-size: 11px; font-weight: bold; color: #6F7682; min-width: 45px;")
        self.gaussian_pct.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        gaussian_prog_layout.addWidget(self.gaussian_pct)
        layout.addLayout(gaussian_prog_layout)

        layout.addSpacing(6)

        # Open Model / Open Folder Buttons
        self.open_buttons_layout = QHBoxLayout()
        self.open_buttons_layout.setSpacing(10)
        self.open_model_btn = QPushButton("  Open Model")
        self.open_model_btn.setIcon(create_vector_icon("reconstruction", QColor("#cbd5e1")))
        self.open_model_btn.setEnabled(False)
        self.open_model_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.open_folder_btn = QPushButton("  Open Folder")
        self.open_folder_btn.setIcon(create_vector_icon("folder", QColor("#cbd5e1")))
        self.open_folder_btn.setEnabled(False)
        self.open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.open_buttons_layout.addWidget(self.open_model_btn)
        self.open_buttons_layout.addWidget(self.open_folder_btn)
        layout.addLayout(self.open_buttons_layout)

        layout.addStretch()
        
        scroll.setWidget(content)
        
        # Outer panel layout
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)
        
        # Adjustable boundaries
        self.setMinimumWidth(300)
        self.setMaximumWidth(320)

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QPen, QColor
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#0E1014"))
        
        # Subtle left border (1px solid rgba(255,255,255,0.04))
        painter.setPen(QPen(QColor(255, 255, 255, 10), 1))
        painter.drawLine(self.rect().topLeft(), self.rect().bottomLeft())
        
        p = self.parent()
        while p:
            if hasattr(p, "noise_pixmap") and p.noise_pixmap:
                painter.drawTiledPixmap(self.rect(), p.noise_pixmap)
                break
            p = p.parent()