from PyQt6.QtWidgets import QFrame, QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QProgressBar, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QPainter, QFont
from ui.viewport import create_vector_icon
from core.project_manager import ProjectManager

class ProjectItemWidget(QWidget):
    def __init__(self, name, date, is_active=False, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Left: Icon container
        icon_lbl = QLabel()
        icon_lbl.setPixmap(create_vector_icon("folder", color=QColor("#5B8CFF"), size=QSize(12, 12)).pixmap(12, 12))
        icon_lbl.setStyleSheet("""
            background-color: #181A1F;
            border: 1px solid rgba(255,255,255,0.04);
            border-radius: 4px;
            min-width: 24px;
            min-height: 24px;
            max-width: 24px;
            max-height: 24px;
        """)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)
        
        # Center: Name and Date
        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-weight: bold; font-size: 12px; color: #f8fafc; background: transparent; border: none;")
        
        date_lbl = QLabel(date)
        date_lbl.setStyleSheet("font-size: 10px; color: #64748b; background: transparent; border: none;")
        
        text_layout.addWidget(name_lbl)
        text_layout.addWidget(date_lbl)
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # Right: Active Pill
        if is_active:
            badge = QLabel("Active")
            badge.setStyleSheet("""
                background-color: rgba(88, 199, 119, 0.15);
                border: 1px solid #58C777;
                border-radius: 4px;
                color: #58C777;
                font-size: 9px;
                font-weight: bold;
                padding: 1px 5px;
            """)
            layout.addWidget(badge)

class ProjectsListWidget(QListWidget):
    """
    QListWidget with a premium empty state when no projects are listed.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ProjectList")
        
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.count() == 0:
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            rect = self.viewport().rect()
            painter.setPen(QColor("#6F7682"))
            font = QFont("Segoe UI", 9)
            painter.setFont(font)
            painter.drawText(
                rect,
                Qt.AlignmentFlag.AlignCenter,
                "No Projects Found"
            )


class Sidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        
        # Scroll Area to prevent clipping on 1080p and high-DPI scaling
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)
        
        # Projects Heading
        projects_header = QHBoxLayout()
        projects_header.setContentsMargins(0, 0, 0, 0)
        
        projects_title = QLabel("Projects")
        projects_title.setObjectName("SectionTitle")
        projects_header.addWidget(projects_title)
        
        projects_header.addStretch()
        
        self.plus_btn = QPushButton()
        self.plus_btn.setIcon(create_vector_icon("plus", QColor("#cbd5e1")))
        self.plus_btn.setIconSize(QSize(10, 10))
        self.plus_btn.setFixedSize(20, 20)
        self.plus_btn.setStyleSheet("padding: 0px; border-radius: 6px; background-color: #1A1D22; border: 1px solid rgba(255,255,255,0.04);")
        self.plus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        projects_header.addWidget(self.plus_btn)
        
        layout.addLayout(projects_header)

        # Search line input
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search projects...")
        layout.addWidget(self.search)

        # Project lists
        self.project_list = ProjectsListWidget()
        self.project_list.setMinimumHeight(200)
        layout.addWidget(self.project_list)
        
        layout.addSpacing(6)

        # Current Project Metadata
        current_title = QLabel("Current Project")
        current_title.setObjectName("SectionTitle")
        layout.addWidget(current_title)

        current_project_card = QFrame()
        current_project_card.setStyleSheet("background: transparent; border: none; padding: 0px;")
        curr_layout = QVBoxLayout(current_project_card)
        curr_layout.setContentsMargins(0, 0, 0, 0)
        curr_layout.setSpacing(4)

        self.current_project_name = QLabel("No Project Loaded")
        self.current_project_name.setStyleSheet("font-weight: bold; font-size: 13px; color: #f8fafc;")
        curr_layout.addWidget(self.current_project_name)

        self.project_info = QLabel("None") # path label mapped to backend
        self.project_info.setStyleSheet("font-size: 11px; color: #475569;")
        self.project_info.setWordWrap(True)
        curr_layout.addWidget(self.project_info)
        
        curr_layout.addSpacing(6)

        # Storage capacity layout
        storage_info_layout = QHBoxLayout()
        self.storage_label = QLabel("0 GB / 0 GB")
        self.storage_label.setStyleSheet("font-size: 11px; color: #64748b;")
        self.storage_pct_label = QLabel("0%")
        self.storage_pct_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #64748b;")
        storage_info_layout.addWidget(self.storage_label)
        storage_info_layout.addStretch()
        storage_info_layout.addWidget(self.storage_pct_label)
        curr_layout.addLayout(storage_info_layout)

        self.storage_bar = QProgressBar()
        self.storage_bar.setValue(0)
        self.storage_bar.setTextVisible(False)
        curr_layout.addWidget(self.storage_bar)

        layout.addWidget(current_project_card)
        layout.addSpacing(6)

        # Quick Actions list
        quick_title = QLabel("Quick Actions")
        quick_title.setObjectName("SectionTitle")
        layout.addWidget(quick_title)

        self.open_folder_btn = QPushButton("  Open Project Folder")
        self.open_folder_btn.setIcon(create_vector_icon("folder", QColor("#cbd5e1")))
        self.open_folder_btn.setIconSize(QSize(12, 12))
        
        self.settings_btn = QPushButton("  Project Settings")
        self.settings_btn.setIcon(create_vector_icon("settings", QColor("#cbd5e1")))
        self.settings_btn.setIconSize(QSize(12, 12))
        
        self.clear_btn = QPushButton("  Clear Cache")
        self.clear_btn.setIcon(create_vector_icon("trash", QColor("#cbd5e1")))
        self.clear_btn.setIconSize(QSize(12, 12))
        
        self.import_btn = QPushButton("  Import Images")
        self.import_btn.setIcon(create_vector_icon("export", QColor("#cbd5e1")))
        self.import_btn.setIconSize(QSize(12, 12))

        for btn in [self.open_folder_btn, self.settings_btn, self.clear_btn, self.import_btn]:
            btn.setStyleSheet("text-align: left; padding-left: 12px; font-size: 12px; font-weight: 600;")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(btn)

        scroll.setWidget(content)
        
        # Outer sidebar layout
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)
        
        # Adjustable sidebar width limits
        self.setMinimumWidth(240)
        self.setMaximumWidth(280)

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QPen, QColor
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#111214"))
        
        # Subtle right border (1px solid rgba(255,255,255,0.04))
        painter.setPen(QPen(QColor(255, 255, 255, 10), 1))
        painter.drawLine(self.rect().topRight(), self.rect().bottomRight())
        
        p = self.parent()
        while p:
            if hasattr(p, "noise_pixmap") and p.noise_pixmap:
                painter.drawTiledPixmap(self.rect(), p.noise_pixmap)
                break
            p = p.parent()

    def load_projects_list(self):
        self.project_list.clear()
        pm = ProjectManager()
        recent = pm.get_recent_projects()
        
        # Find the active project name from parent Workspace
        active_project_name = None
        p = self.parent()
        while p:
            if hasattr(p, "current_project"):
                active_project_name = p.current_project
                break
            p = p.parent()
            
        for p in recent:
            item = QListWidgetItem()
            name = p.get("name")
            date_str = p.get("last_opened", "")
            if date_str and len(date_str) > 16:
                date_str = date_str[:16] # Keep YYYY-MM-DD HH:MM
                
            is_active = (name == active_project_name)
            
            widget = ProjectItemWidget(name, date_str, is_active)
            item.setSizeHint(QSize(150, 42)) # Adjust height of item card
            self.project_list.addItem(item)
            self.project_list.setItemWidget(item, widget)