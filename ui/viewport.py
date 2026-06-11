import math
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QListWidget
from PyQt6.QtCore import Qt, QSize, QPoint, QRect, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QPixmap, QIcon, QPainterPath, QColor, QFont, QRadialGradient

# =====================================================
# VECTOR ICON GENERATOR
# =====================================================
def create_vector_icon(icon_type, color=QColor("#9DA3AE"), size=QSize(16, 16)):
    """
    Dynamically generates a QIcon with clean, minimalist vector drawings.
    Ensures zero emojis and professional workstation appearance.
    """
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    pen = QPen(color, 1.8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    
    w, h = size.width(), size.height()
    cx, cy = w / 2.0, h / 2.0
    
    if icon_type == "folder":
        path = QPainterPath()
        path.moveTo(2, 4)
        path.lineTo(7, 4)
        path.lineTo(9, 6)
        path.lineTo(14, 6)
        path.quadTo(15, 6, 15, 7)
        path.lineTo(15, 13)
        path.quadTo(15, 14, 14, 14)
        path.lineTo(2, 14)
        path.quadTo(1, 14, 1, 13)
        path.lineTo(1, 5)
        path.quadTo(1, 4, 2, 4)
        painter.drawPath(path)
        
    elif icon_type == "timer":
        painter.drawEllipse(QPointF(cx, cy + 1), 5.5, 5.5)
        painter.drawLine(QPointF(cx, cy - 4.5), QPointF(cx, cy - 6))
        painter.drawLine(QPointF(cx - 1.5, cy - 6), QPointF(cx + 1.5, cy - 6))
        painter.drawLine(QPointF(cx, cy + 1), QPointF(cx + 2.5, cy - 1))
        
    elif icon_type == "database":
        painter.drawEllipse(QPointF(cx, 4.5), 5.5, 2)
        painter.drawEllipse(QPointF(cx, 9), 5.5, 2)
        painter.drawEllipse(QPointF(cx, 13.5), 5.5, 2)
        painter.drawLine(QPointF(cx - 5.5, 4.5), QPointF(cx - 5.5, 13.5))
        painter.drawLine(QPointF(cx + 5.5, 4.5), QPointF(cx + 5.5, 13.5))
        
    elif icon_type == "gpu":
        painter.drawRect(QRectF(cx - 5, cy - 5, 10, 10))
        painter.drawRect(QRectF(cx - 2.5, cy - 2.5, 5, 5))
        for offset in [-3, 0, 3]:
            painter.drawLine(QPointF(cx + offset, cy - 5), QPointF(cx + offset, cy - 7))
            painter.drawLine(QPointF(cx + offset, cy + 5), QPointF(cx + offset, cy + 7))
            painter.drawLine(QPointF(cx - 5, cy + offset), QPointF(cx - 7, cy + offset))
            painter.drawLine(QPointF(cx + 5, cy + offset), QPointF(cx + 7, cy + offset))
            
    elif icon_type == "rtsp" or icon_type == "network":
        painter.drawEllipse(QPointF(cx, cy), 6, 6)
        painter.drawLine(QPointF(cx - 6, cy), QPointF(cx + 6, cy))
        painter.drawLine(QPointF(cx, cy - 6), QPointF(cx, cy + 6))
        painter.drawEllipse(QPointF(cx, cy), 2.5, 6)
        
    elif icon_type == "settings":
        painter.drawEllipse(QPointF(cx, cy), 3, 3)
        for i in range(8):
            angle = i * math.pi / 4
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            painter.drawLine(QPointF(cx + 4 * cos_a, cy + 4 * sin_a), QPointF(cx + 6.5 * cos_a, cy + 6.5 * sin_a))
            
    elif icon_type == "help":
        painter.drawEllipse(QPointF(cx, cy), 7, 7)
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        painter.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "?")
        
    elif icon_type == "plus":
        painter.drawLine(QPointF(cx - 4, cy), QPointF(cx + 4, cy))
        painter.drawLine(QPointF(cx, cy - 4), QPointF(cx, cy + 4))
        
    elif icon_type == "trash":
        painter.drawLine(QPointF(cx - 5, cy - 4), QPointF(cx + 5, cy - 4))
        painter.drawRect(QRectF(cx - 1.5, cy - 6, 3, 2))
        painter.drawRect(QRectF(cx - 3.5, cy - 4, 7, 9))
        painter.drawLine(QPointF(cx - 1, cy - 1), QPointF(cx - 1, cy + 3))
        painter.drawLine(QPointF(cx + 1, cy - 1), QPointF(cx + 1, cy + 3))
        
    elif icon_type == "play":
        path = QPainterPath()
        path.moveTo(cx - 2.5, cy - 4)
        path.lineTo(cx + 4.5, cy)
        path.lineTo(cx - 2.5, cy + 4)
        path.closeSubpath()
        painter.setBrush(QBrush(color))
        painter.drawPath(path)
        
    elif icon_type == "stop":
        painter.setBrush(QBrush(color))
        painter.drawRect(QRectF(cx - 3.5, cy - 3.5, 7, 7))
        
    elif icon_type == "pause":
        painter.setBrush(QBrush(color))
        painter.drawRect(QRectF(cx - 3, cy - 4, 2, 8))
        painter.drawRect(QRectF(cx + 1, cy - 4, 2, 8))
        
    elif icon_type == "camera":
        painter.drawRect(QRectF(cx - 6, cy - 2, 12, 6.5))
        painter.drawEllipse(QPointF(cx, cy + 1), 2.2, 2.2)
        painter.drawRect(QRectF(cx - 2.5, cy - 4, 5, 2))
        
    elif icon_type == "refresh":
        painter.drawArc(QRectF(cx - 5, cy - 5, 10, 10), 45 * 16, 270 * 16)
        path = QPainterPath()
        path.moveTo(cx + 2, cy - 3.5)
        path.lineTo(cx + 4.5, cy - 1)
        path.lineTo(cx + 6.5, cy - 4)
        painter.drawPath(path)

    elif icon_type == "dashboard":
        painter.drawRect(QRectF(cx - 5, cy - 5, 4, 4))
        painter.drawRect(QRectF(cx + 1, cy - 5, 4, 4))
        painter.drawRect(QRectF(cx - 5, cy + 1, 4, 4))
        painter.drawRect(QRectF(cx + 1, cy + 1, 4, 4))

    elif icon_type == "reconstruction":
        painter.drawLine(QPointF(cx, cy - 6), QPointF(cx + 5, cy - 3.5))
        painter.drawLine(QPointF(cx + 5, cy - 3.5), QPointF(cx + 5, cy + 2.5))
        painter.drawLine(QPointF(cx + 5, cy + 2.5), QPointF(cx, cy + 5))
        painter.drawLine(QPointF(cx, cy + 5), QPointF(cx - 5, cy + 2.5))
        painter.drawLine(QPointF(cx - 5, cy + 2.5), QPointF(cx - 5, cy - 3.5))
        painter.drawLine(QPointF(cx - 5, cy - 3.5), QPointF(cx, cy - 6))
        painter.drawLine(QPointF(cx, cy - 6), QPointF(cx, cy + 5))
        painter.drawLine(QPointF(cx, cy - 0.5), QPointF(cx + 5, cy - 3.5))
        painter.drawLine(QPointF(cx, cy - 0.5), QPointF(cx - 5, cy - 3.5))

    elif icon_type == "viewer":
        path = QPainterPath()
        path.moveTo(cx - 7, cy)
        path.quadTo(cx, cy - 5, cx + 7, cy)
        path.quadTo(cx, cy + 5, cx - 7, cy)
        painter.drawPath(path)
        painter.drawEllipse(QPointF(cx, cy), 2, 2)

    elif icon_type == "gaussian":
        painter.drawEllipse(QPointF(cx, cy), 2.5, 2.5)
        painter.drawEllipse(QPointF(cx, cy), 5, 5)

    elif icon_type == "export":
        painter.drawRect(QRectF(cx - 5, cy - 1, 10, 6))
        painter.drawLine(QPointF(cx, cy - 1), QPointF(cx, cy - 6))
        painter.drawLine(QPointF(cx - 2.5, cy - 3.5), QPointF(cx, cy - 6))
        painter.drawLine(QPointF(cx + 2.5, cy - 3.5), QPointF(cx, cy - 6))

    elif icon_type == "cancel" or icon_type == "cross":
        painter.drawLine(QPointF(cx - 4, cy - 4), QPointF(cx + 4, cy + 4))
        painter.drawLine(QPointF(cx + 4, cy - 4), QPointF(cx - 4, cy + 4))

    painter.end()
    return QIcon(pixmap)


# =====================================================
# VIEWPORT COMPONENT
# =====================================================
class ViewportWidget(QWidget):
    """
    A custom painted video canvas widget with float overlays and aspect-ratio checking.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("VideoViewport")
        self._pixmap = None
        
        # Float layouts
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Top status overlays
        top_layout = QHBoxLayout()
        self.live_overlay = QLabel("● LIVE")
        self.live_overlay.setStyleSheet("""
            background-color: rgba(5, 6, 8, 0.9);
            color: #58C777;
            font-size: 11px;
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 4px;
            border: 1px solid rgba(255,255,255,0.04);
        """)
        self.live_overlay.hide()
        top_layout.addWidget(self.live_overlay)
        
        top_layout.addStretch()
        
        self.fps_overlay = QLabel("FPS: 0.0")
        self.fps_overlay.setStyleSheet("""
            background-color: rgba(5, 6, 8, 0.9);
            color: #E4E7EB;
            font-size: 11px;
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 4px;
            border: 1px solid rgba(255,255,255,0.04);
        """)
        self.fps_overlay.hide()
        top_layout.addWidget(self.fps_overlay)
        
        layout.addLayout(top_layout)
        layout.addStretch()

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        if pixmap and not pixmap.isNull():
            self.live_overlay.show()
            self.fps_overlay.show()
            self.fps_overlay.setText("FPS: 29.7")
        else:
            self.live_overlay.hide()
            self.fps_overlay.hide()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        rect = self.rect()
        painter.fillRect(rect, QColor("#050608"))
        
        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (rect.width() - scaled.width()) // 2
            y = (rect.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            cx, cy = rect.center().x(), rect.center().y()
            painter.setPen(QColor("#E4E7EB"))
            font_title = QFont("Segoe UI", 11, QFont.Weight.Bold)
            painter.setFont(font_title)
            painter.drawText(
                QRect(0, cy + 18, rect.width(), 24),
                Qt.AlignmentFlag.AlignCenter,
                "No Active Capture Session"
            )
            
            font_subtitle = QFont("Segoe UI", 9)
            painter.setFont(font_subtitle)
            painter.setPen(QColor("#6F7682"))
            painter.drawText(
                QRect(10, cy + 42, rect.width() - 20, 40),
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                "Connect an RTSP stream and start capture to begin spatial reconstruction."
            )

        # Draw ultra subtle vignette overlay (darker corners, soft center)
        vignette = QRadialGradient(QPointF(rect.center()), math.sqrt(rect.width()**2 + rect.height()**2) / 2.0)
        vignette.setColorAt(0.0, QColor(0, 0, 0, 0))
        vignette.setColorAt(0.65, QColor(0, 0, 0, 35))
        vignette.setColorAt(1.0, QColor(0, 0, 0, 150))
        painter.fillRect(rect, vignette)

        # Draw 1px solid rgba(255,255,255,0.03) border
        pen = QPen(QColor(255, 255, 255, 8), 1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect.adjusted(0, 0, -1, -1))


# =====================================================
# RECENT FRAMES TIMELINE
# =====================================================
class RecentFramesListWidget(QListWidget):
    """
    Horizontal list of captured image frames with a workstation empty state.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RecentFramesList")
        
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.count() == 0:
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            rect = self.viewport().rect()
            painter.setPen(QColor("#334155"))
            font = QFont("Segoe UI", 9)
            painter.setFont(font)
            painter.drawText(
                rect,
                Qt.AlignmentFlag.AlignCenter,
                "No Captured Frames Yet"
            )