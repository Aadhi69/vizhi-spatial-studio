import os
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QLabel, QLineEdit, QSpinBox, QComboBox, QCheckBox, QPushButton, QFileDialog
from PyQt6.QtCore import Qt
from core.config_manager import ConfigManager
from core.notification_manager import NotificationManager

class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setFixedSize(500, 420)
        self.setModal(True)
        self.config_manager = ConfigManager()
        self.build_ui()

    def build_ui(self):
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
            QLineEdit, QComboBox, QSpinBox {
                background-color: #0D0F12;
                border: 1px solid rgba(255,255,255,0.04);
                border-radius: 6px;
                padding: 6px;
                color: #E6E6E6;
                font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid #5B8CFF;
            }
            QCheckBox {
                color: #E6E6E6;
                font-size: 12px;
            }
            QCheckBox::indicator {
                background-color: #0D0F12;
                border: 1px solid rgba(255,255,255,0.04);
                width: 14px;
                height: 14px;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #5B8CFF;
                border: 1px solid rgba(255,255,255,0.08);
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
            QPushButton#SaveBtn {
                background-color: #5B8CFF;
                border: 1px solid rgba(255,255,255,0.04);
                color: #ffffff;
            }
            QPushButton#SaveBtn:hover {
                background-color: #6EA8FE;
                border: 1px solid rgba(255,255,255,0.08);
            }
            QTabWidget::pane {
                border: 1px solid rgba(255,255,255,0.04);
                top: -1px;
                background-color: #111214;
            }
            QTabBar::tab {
                background-color: transparent;
                color: #6F7682;
                padding: 8px 14px;
                font-weight: 600;
                font-size: 11px;
                border-bottom: 2px solid transparent;
            }
            QTabBar::tab:hover {
                color: #E6E6E6;
            }
            QTabBar::tab:selected {
                color: #5B8CFF;
                border-bottom: 2px solid #5B8CFF;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        self.tabs = QTabWidget()
        
        # 1. General Tab
        self.tab_general = QWidget()
        gen_layout = QVBoxLayout(self.tab_general)
        gen_layout.setSpacing(12)
        
        rtsp_lbl = QLabel("Default RTSP Stream URL")
        self.rtsp_input = QLineEdit(self.config_manager.get("default_rtsp"))
        gen_layout.addWidget(rtsp_lbl)
        gen_layout.addWidget(self.rtsp_input)
        
        self.autosave_check = QCheckBox("Enable Workspace Auto-Save on Close")
        self.autosave_check.setChecked(self.config_manager.get("autosave"))
        gen_layout.addWidget(self.autosave_check)
        gen_layout.addStretch()
        self.tabs.addTab(self.tab_general, "General")

        # 2. Capture Tab
        self.tab_capture = QWidget()
        cap_layout = QVBoxLayout(self.tab_capture)
        cap_layout.setSpacing(12)
        
        interval_lbl = QLabel("Default Ingestion Frame Interval")
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1000)
        self.interval_spin.setValue(self.config_manager.get("capture_interval"))
        cap_layout.addWidget(interval_lbl)
        cap_layout.addWidget(self.interval_spin)
        cap_layout.addStretch()
        self.tabs.addTab(self.tab_capture, "Capture")

        # 3. Reconstruction Tab
        self.tab_recon = QWidget()
        rec_layout = QVBoxLayout(self.tab_recon)
        rec_layout.setSpacing(12)
        
        gpu_lbl = QLabel("Reconstruction Compute Device")
        self.gpu_combo = QComboBox()
        from core.gpu_monitor import get_gpu_info
        try:
            gpu_name = get_gpu_info()[0]["name"]
        except Exception:
            gpu_name = "NVIDIA GeForce GPU"
        self.gpu_combo.addItems([f"CUDA:0 ({gpu_name})", "CPU Fallback"])
        self.gpu_combo.setCurrentText(self.config_manager.get("gpu_selection"))
        rec_layout.addWidget(gpu_lbl)
        rec_layout.addWidget(self.gpu_combo)
        rec_layout.addStretch()
        self.tabs.addTab(self.tab_recon, "COLMAP")

        # 4. Paths Tab
        self.tab_paths = QWidget()
        paths_layout = QVBoxLayout(self.tab_paths)
        paths_layout.setSpacing(12)
        
        export_lbl = QLabel("Default Export Path")
        export_row = QHBoxLayout()
        self.export_input = QLineEdit(self.config_manager.get("default_export_path"))
        btn_browse = QPushButton("Browse")
        btn_browse.clicked.connect(self.browse_export_path)
        export_row.addWidget(self.export_input)
        export_row.addWidget(btn_browse)
        paths_layout.addWidget(export_lbl)
        paths_layout.addLayout(export_row)
        
        cache_lbl = QLabel("Cache Limit Boundary (GB)")
        self.cache_spin = QSpinBox()
        self.cache_spin.setRange(1, 100)
        self.cache_spin.setValue(self.config_manager.get("cache_limit_gb"))
        paths_layout.addWidget(cache_lbl)
        paths_layout.addWidget(self.cache_spin)
        paths_layout.addStretch()
        self.tabs.addTab(self.tab_paths, "Paths & Cache")

        layout.addWidget(self.tabs)
        
        # Save / Cancel Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("Save")
        btn_save.setObjectName("SaveBtn")
        btn_save.clicked.connect(self.save_preferences)
        
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def browse_export_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Default Export Directory", self.export_input.text())
        if path:
            self.export_input.setText(os.path.normpath(path))

    def save_preferences(self):
        try:
            self.config_manager.set("default_rtsp", self.rtsp_input.text().strip())
            self.config_manager.set("autosave", self.autosave_check.isChecked())
            self.config_manager.set("capture_interval", self.interval_spin.value())
            self.config_manager.set("gpu_selection", self.gpu_combo.currentText())
            self.config_manager.set("default_export_path", self.export_input.text().strip())
            self.config_manager.set("cache_limit_gb", self.cache_spin.value())
            self.config_manager.save()
            NotificationManager().show_notification("Preferences saved successfully", "success")
            self.accept()
        except Exception as e:
            NotificationManager().show_notification(f"Failed to save preferences: {e}", "error")
