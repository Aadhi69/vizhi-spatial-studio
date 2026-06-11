from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor
from ui.viewport import create_vector_icon  # we'll place icon gen in viewport or separate file, viewport is fine

# We'll import create_vector_icon from viewport.py since it has the vector icon function defined
# Let's import it locally inside methods to avoid circular references if necessary.

class LogoIconWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedSize(32, 32)

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QPen, QPainterPath, QColor
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        brand_color = QColor("#5B8CFF")
        secondary_color = QColor("#6EA8FE")
        
        # Outer inverted triangle with top-left gap
        outer_pen = QPen(brand_color, 1.8)
        painter.setPen(outer_pen)
        
        # Outer path: top-left gap horizontal line (9, 6) -> top-right (28, 6) -> bottom apex (16, 27) -> left end (4, 10)
        outer_path = QPainterPath()
        outer_path.moveTo(9, 6)
        outer_path.lineTo(28, 6)
        outer_path.lineTo(16, 27)
        outer_path.lineTo(4, 10)
        painter.drawPath(outer_path)
        
        # Inner parallel inverted triangle chevron
        inner_pen = QPen(secondary_color, 1.0)
        painter.setPen(inner_pen)
        
        # Inner path: top-left gap horizontal line (12, 10) -> top-right (24, 10) -> bottom apex (16, 22) -> left end (7, 13)
        inner_path = QPainterPath()
        inner_path.moveTo(12, 10)
        inner_path.lineTo(24, 10)
        inner_path.lineTo(16, 22)
        inner_path.lineTo(7, 13)
        painter.drawPath(inner_path)


class TopBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setFixedHeight(64)
        self.build_ui()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QPen
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#111214"))
        
        # Subtle bottom border (1px solid rgba(255,255,255,0.04))
        painter.setPen(QPen(QColor(255, 255, 255, 10), 1))
        painter.drawLine(self.rect().bottomLeft(), self.rect().bottomRight())
        
        p = self.parent()
        while p:
            if hasattr(p, "noise_pixmap") and p.noise_pixmap:
                painter.drawTiledPixmap(self.rect(), p.noise_pixmap)
                break
            p = p.parent()

    def build_ui(self):
        from ui.viewport import create_vector_icon
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(14)

        # Logo text
        logo_layout = QHBoxLayout()
        logo_layout.setSpacing(10)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        
        logo_icon = LogoIconWidget()
        logo_layout.addWidget(logo_icon)
        
        logo_text_layout = QVBoxLayout()
        logo_text_layout.setSpacing(0)
        logo_text_layout.setContentsMargins(0, 0, 0, 0)
        
        logo_text = QLabel("VIZHI")
        logo_text.setObjectName("LogoText")
        logo_sub = QLabel("SPATIAL STUDIO")
        logo_sub.setObjectName("LogoSub")
        
        logo_text_layout.addWidget(logo_text)
        logo_text_layout.addWidget(logo_sub)
        logo_layout.addLayout(logo_text_layout)
        
        layout.addLayout(logo_layout)
        layout.addSpacing(30)

        # Custom Workstation Dropdown Menus
        menu_layout = QHBoxLayout()
        menu_layout.setSpacing(2)
        
        self.btn_menu_file = QPushButton("File")
        self.btn_menu_edit = QPushButton("Edit")
        self.btn_menu_view = QPushButton("View")
        self.btn_menu_tools = QPushButton("Tools")
        self.btn_menu_help = QPushButton("Help")
        
        for btn in [self.btn_menu_file, self.btn_menu_edit, self.btn_menu_view, self.btn_menu_tools, self.btn_menu_help]:
            btn.setObjectName("TopbarMenuBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            menu_layout.addWidget(btn)
            
        layout.addLayout(menu_layout)
        layout.addSpacing(20)

        # Navigation Tabs
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(6)
        nav_layout.setContentsMargins(0, 0, 0, 0)

        nav_tabs = [
            ("Dashboard", "dashboard", True),
            ("Capture", "camera", False),
            ("Reconstruction", "reconstruction", False),
            ("Viewer", "viewer", False),
            ("Gaussian", "gaussian", False),
            ("Export", "export", False)
        ]

        self.nav_buttons = {}
        for key, icon_type, active in nav_tabs:
            btn = QPushButton(f" {key.upper()}")
            btn.setObjectName("NavButton")
            btn.setIcon(create_vector_icon(icon_type, color=QColor("#5B8CFF") if active else QColor("#64748b")))
            btn.setIconSize(QSize(14, 14))
            btn.setProperty("active", active)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            nav_layout.addWidget(btn)
            self.nav_buttons[key] = btn

        layout.addLayout(nav_layout)
        layout.addStretch()

        # System Monitor Box
        self.sys_card = QFrame()
        self.sys_card.setObjectName("MetricCard")
        self.sys_card.setFixedHeight(40)
        self.sys_card.setFixedWidth(200)
        
        sys_layout = QVBoxLayout(self.sys_card)
        sys_layout.setContentsMargins(12, 3, 12, 3)
        sys_layout.setSpacing(0)
        
        sys_title = QLabel("System Monitor")
        sys_title.setStyleSheet("font-size: 9px; color: #6F7682; font-weight: bold; text-transform: uppercase;")
        sys_layout.addWidget(sys_title)
        
        sys_details = QHBoxLayout()
        sys_details.setSpacing(6)
        sys_details.setContentsMargins(0, 0, 0, 0)
        
        green_dot = QLabel("●")
        green_dot.setStyleSheet("color: #58C777; font-size: 8px; background: transparent;")
        
        self.sys_gpu_label = QLabel("GPU 0%")
        self.sys_gpu_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #58C777; background: transparent;")
        
        self.sys_vram_label = QLabel("VRAM 0MB")
        self.sys_vram_label.setStyleSheet("font-size: 11px; color: #E6E6E6; background: transparent;")
        
        sys_details.addWidget(green_dot)
        sys_details.addWidget(self.sys_gpu_label)
        sys_details.addWidget(self.sys_vram_label)
        sys_details.addStretch()
        sys_layout.addLayout(sys_details)
        
        layout.addWidget(self.sys_card)

        # Settings & Help Icon Buttons
        self.settings_btn = QPushButton()
        self.settings_btn.setObjectName("IconButton")
        self.settings_btn.setIcon(create_vector_icon("settings", QColor("#cbd5e1")))
        self.settings_btn.setIconSize(QSize(16, 16))
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.settings_btn)

        self.btn_help = QPushButton()
        self.btn_help.setObjectName("IconButton")
        self.btn_help.setIcon(create_vector_icon("help", QColor("#cbd5e1")))
        self.btn_help.setIconSize(QSize(16, 16))
        self.btn_help.setFixedSize(32, 32)
        self.btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.btn_help)