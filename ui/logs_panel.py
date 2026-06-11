import re
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QTabWidget, QWidget, QTextEdit
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor
from ui.viewport import create_vector_icon

class ConsoleLogTextEdit(QTextEdit):
    """
    Monospace terminal output logger with automatic log syntax coloring.
    INFO = cyan, SUCCESS = green, WARNING = yellow, ERROR = red.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setObjectName("ConsoleLogText")
        
        from PyQt6.QtGui import QFont
        font = QFont("JetBrains Mono")
        # Check if the font is available, if not fallback
        from PyQt6.QtGui import QFontDatabase
        available = QFontDatabase.families()
        if "JetBrains Mono" not in available:
            if "Cascadia Code" in available:
                font = QFont("Cascadia Code")
            else:
                font = QFont("Consolas")
        font.setPointSize(9)
        self.setFont(font)
        
    def append(self, text):
        # Match log layout: [HH:MM:SS] [LEVEL] Message
        match = re.match(r"^(\[\d{2}:\d{2}:\d{2}\])\s+\[([A-Z]+)\]\s+(.*)$", text)
        if match:
            timestamp, level, msg = match.groups()
            level = level.upper()
            if level == "INFO":
                color = "#5B8CFF" # Primary Accent
            elif level == "SUCCESS":
                color = "#58C777" # Success Accent
            elif level == "WARNING":
                color = "#D9A441"
            elif level == "ERROR":
                color = "#D95C5C"
            elif level == "COLMAP":
                color = "#5B8CFF" # Primary Accent
            elif level == "GAUSSIAN":
                color = "#6EA8FE" # Secondary Accent
            else:
                color = "#6F7682"
                
            html = f'<span style="color:#5C6370;">{timestamp}</span> &nbsp;<span style="color:{color}; font-weight:bold;">[{level}]</span> &nbsp;<span style="color:#C8CCD4; line-height:130%;">{msg}</span>'
            super().insertHtml(html + "<br>")
            self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        else:
            super().append(text)


class LogsPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ConsoleCard")
        self.build_ui()
        
    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QPen, QColor
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#0B0B0D"))
        
        # Subtle top border (1px solid rgba(255,255,255,0.04))
        painter.setPen(QPen(QColor(255, 255, 255, 10), 1))
        painter.drawLine(self.rect().topLeft(), self.rect().topRight())
        
        p = self.parent()
        while p:
            if hasattr(p, "noise_pixmap") and p.noise_pixmap:
                painter.drawTiledPixmap(self.rect(), p.noise_pixmap)
                break
            p = p.parent()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(6)

        self.tabs = QTabWidget()

        self.logs_text = ConsoleLogTextEdit()
        self.tasks_text = ConsoleLogTextEdit()
        self.notifications_text = ConsoleLogTextEdit()

        self.tabs.addTab(self.logs_text, "System Logs")
        self.tabs.addTab(self.tasks_text, "Tasks")
        self.tabs.addTab(self.notifications_text, "Notifications")

        # Top Right console corner widgets
        corner_widget = QWidget()
        corner_layout = QHBoxLayout(corner_widget)
        corner_layout.setContentsMargins(0, 0, 4, 0)
        corner_layout.setSpacing(8)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("NavButton")
        self.clear_btn.setIcon(create_vector_icon("trash", QColor("#64748b")))
        self.clear_btn.setIconSize(QSize(11, 11))
        self.clear_btn.setStyleSheet("font-size: 11px; padding: 4px 8px;")
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.export_btn = QPushButton("Export Logs")
        self.export_btn.setObjectName("NavButton")
        self.export_btn.setIcon(create_vector_icon("export", QColor("#64748b")))
        self.export_btn.setIconSize(QSize(11, 11))
        self.export_btn.setStyleSheet("font-size: 11px; padding: 4px 8px;")
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Logs", "Info", "Success", "Warning", "Error"])
        self.filter_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.filter_combo.setStyleSheet("""
            background-color: #050608;
            border: 1px solid rgba(255,255,255,0.04);
            border-radius: 4px;
            padding: 2px 20px 2px 8px;
            font-size: 11px;
            color: #E4E7EB;
        """)
        
        corner_layout.addWidget(self.clear_btn)
        corner_layout.addWidget(self.export_btn)
        corner_layout.addWidget(self.filter_combo)
        
        self.tabs.setCornerWidget(corner_widget, Qt.Corner.TopRightCorner)
        layout.addWidget(self.tabs)
