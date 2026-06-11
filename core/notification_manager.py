from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import QObject, Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QSize

class NotificationToast(QWidget):
    def __init__(self, parent, message, severity="info"):
        super().__init__(parent)
        self.severity = severity.lower()
        self.setWindowFlags(Qt.WindowType.SubWindow | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Style matching matte graphite theme
        border_color = "#1e293b"
        icon_color = "#3b82f6"
        
        if self.severity == "success":
            icon_color = "#34d399"
        elif self.severity == "warning":
            icon_color = "#fbbf24"
        elif self.severity == "error":
            icon_color = "#f87171"

        # Main frame
        self.container = QWidget(self)
        self.container.setObjectName("ToastContainer")
        self.container.setStyleSheet(f"""
            QWidget#ToastContainer {{
                background-color: #0b111e;
                border: 1px solid #1c2535;
                border-left: 4px solid {icon_color};
                border-radius: 6px;
            }}
        """)
        
        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # Status text
        self.label = QLabel(message)
        self.label.setStyleSheet("""
            color: #cbd5e1;
            font-size: 12px;
            font-weight: 600;
        """)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)

        # Set size
        self.setFixedSize(280, 50)

        # Opacity effect for fade transition
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)

        # Animations
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.pos_anim = QPropertyAnimation(self, b"pos")

    def show_toast(self, target_pos):
        self.move(target_pos + QPoint(0, 20)) # Start slightly lower for slide-up
        self.show()

        # Fade animation
        self.fade_anim.setDuration(300)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Position animation
        self.pos_anim.setDuration(300)
        self.pos_anim.setStartValue(self.pos())
        self.pos_anim.setEndValue(target_pos)
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.fade_anim.start()
        self.pos_anim.start()

    def hide_toast(self, callback):
        self.fade_anim.setDuration(250)
        self.fade_anim.setStartValue(self.opacity_effect.opacity())
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.InCubic)

        # Slight downward slide on exit
        self.pos_anim.setDuration(250)
        self.pos_anim.setStartValue(self.pos())
        self.pos_anim.setEndValue(self.pos() + QPoint(0, 10))
        self.pos_anim.setEasingCurve(QEasingCurve.Type.InCubic)

        self.fade_anim.finished.connect(callback)
        self.fade_anim.start()
        self.pos_anim.start()


class NotificationManager(QObject):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(NotificationManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.parent_window = None
            cls._instance.active_toasts = []
            cls._instance.queue = []
        return cls._instance

    def initialize(self, parent_window):
        self.parent_window = parent_window

    def show_notification(self, message, severity="info"):
        if not self.parent_window:
            print(f"[{severity.upper()}] {message}")
            return
            
        toast = NotificationToast(self.parent_window, message, severity)
        self.queue.append(toast)
        self.process_queue()

    def process_queue(self):
        if not self.queue:
            return
        # Display max 3 toasts concurrently
        if len(self.active_toasts) >= 3:
            return
            
        toast = self.queue.pop(0)
        self.active_toasts.append(toast)
        
        # Calculate target position in bottom-right corner of parent window
        self.reposition_toasts()
        
        # Auto-dismiss timer
        timer = QTimer(toast)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self.dismiss_toast(toast))
        timer.start(4000)

    def reposition_toasts(self):
        if not self.parent_window:
            return
            
        parent_rect = self.parent_window.rect()
        base_x = parent_rect.width() - 300
        base_y = parent_rect.height() - 70 # Margin for status bar
        
        for idx, toast in enumerate(self.active_toasts):
            target_y = base_y - (idx * 60)
            target_pos = QPoint(base_x, target_y)
            if toast.isVisible():
                # Animate position adjust if already visible
                toast.pos_anim.stop()
                toast.pos_anim.setDuration(200)
                toast.pos_anim.setStartValue(toast.pos())
                toast.pos_anim.setEndValue(target_pos)
                toast.pos_anim.start()
            else:
                toast.show_toast(target_pos)

    def dismiss_toast(self, toast):
        if toast in self.active_toasts:
            toast.hide_toast(lambda: self.on_toast_faded(toast))

    def on_toast_faded(self, toast):
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
        toast.deleteLater()
        self.reposition_toasts()
        self.process_queue()
