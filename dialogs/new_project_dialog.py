import os
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QTextEdit, QFileDialog
from PyQt6.QtCore import Qt, QSize
from core.project_manager import ProjectManager
from core.notification_manager import NotificationManager

class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Project")
        self.setFixedSize(450, 420)
        self.setModal(True)
        self.project_path = None
        self.build_ui()

    def build_ui(self):
        # Dialog is styled to match the dark graphite workspace theme
        self.setStyleSheet("""
            QDialog {
                background-color: #111214;
                border: 1px solid rgba(255,255,255,0.04);
            }
            QLabel {
                color: #9DA3AE;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
                text-transform: uppercase;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                background-color: #0D0F12;
                border: 1px solid rgba(255,255,255,0.04);
                border-radius: 6px;
                padding: 6px;
                color: #E6E6E6;
                font-size: 12px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid #5B8CFF;
            }
            QPushButton {
                background-color: #1A1D22;
                border: 1px solid rgba(255,255,255,0.04);
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
                color: #E6E6E6;
            }
            QPushButton:hover {
                background-color: #23272E;
                border: 1px solid rgba(255,255,255,0.08);
                color: #ffffff;
            }
            QPushButton#CreateBtn {
                background-color: #5B8CFF;
                border: 1px solid rgba(255,255,255,0.04);
                color: #ffffff;
            }
            QPushButton#CreateBtn:hover {
                background-color: #6EA8FE;
                border: 1px solid rgba(255,255,255,0.08);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Name
        name_layout = QVBoxLayout()
        name_lbl = QLabel("Project Name")
        self.name_input = QLineEdit("MySpatialCapture_01")
        name_layout.addWidget(name_lbl)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Location
        loc_layout = QVBoxLayout()
        loc_lbl = QLabel("Project Location")
        loc_input_layout = QHBoxLayout()
        self.loc_input = QLineEdit(r"D:\vizhi-spatial-software\datasets")
        btn_browse = QPushButton("Browse")
        btn_browse.clicked.connect(self.browse_location)
        loc_input_layout.addWidget(self.loc_input)
        loc_input_layout.addWidget(btn_browse)
        loc_layout.addWidget(loc_lbl)
        loc_layout.addLayout(loc_input_layout)
        layout.addLayout(loc_layout)

        # Description
        desc_layout = QVBoxLayout()
        desc_lbl = QLabel("Description")
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Optional project description notes...")
        self.desc_input.setMaximumHeight(60)
        desc_layout.addWidget(desc_lbl)
        desc_layout.addWidget(self.desc_input)
        layout.addLayout(desc_layout)

        # Horizontal layouts for settings
        settings_row = QHBoxLayout()
        settings_row.setSpacing(12)

        # Capture Type
        type_layout = QVBoxLayout()
        type_lbl = QLabel("Capture Type")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["RTSP Stream", "Webcam/Local", "Image Dataset"])
        type_layout.addWidget(type_lbl)
        type_layout.addWidget(self.type_combo)
        settings_row.addLayout(type_layout)

        # Auto save interval
        interval_layout = QVBoxLayout()
        interval_lbl = QLabel("Auto-Save Every (Frames)")
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 100)
        self.interval_spin.setValue(5)
        interval_layout.addWidget(interval_lbl)
        interval_layout.addWidget(self.interval_spin)
        settings_row.addLayout(interval_layout)

        layout.addLayout(settings_row)
        layout.addStretch()

        # Dialog Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_create = QPushButton("Create")
        btn_create.setObjectName("CreateBtn")
        btn_create.clicked.connect(self.create_project)
        
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_create)
        layout.addLayout(btn_row)

    def browse_location(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Project Folder Location", self.loc_input.text())
        if dir_path:
            self.loc_input.setText(os.path.normpath(dir_path))

    def create_project(self):
        name = self.name_input.text().strip()
        location = self.loc_input.text().strip()
        
        if not name:
            NotificationManager().show_notification("Project name cannot be empty", "error")
            return
            
        if not os.path.exists(location):
            try:
                os.makedirs(location, exist_ok=True)
            except Exception as e:
                NotificationManager().show_notification(f"Invalid path location: {e}", "error")
                return
                
        try:
            pm = ProjectManager()
            self.project_path = pm.create_project(
                name=name,
                location=location,
                description=self.desc_input.toPlainText().strip(),
                capture_type=self.type_combo.currentText(),
                auto_save_interval=self.interval_spin.value()
            )
            NotificationManager().show_notification(f"Project '{name}' created successfully", "success")
            self.accept()
        except Exception as e:
            NotificationManager().show_notification(f"Failed to create project: {e}", "error")
