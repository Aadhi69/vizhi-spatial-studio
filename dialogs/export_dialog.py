import os
import time
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QProgressBar, QFileDialog
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from core.notification_manager import NotificationManager

class ExportWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self, export_type, dest_path):
        super().__init__()
        self.export_type = export_type
        self.dest_path = dest_path

    def run(self):
        try:
            # Simulate a real pipeline export process
            for i in range(1, 101):
                time.sleep(0.015) # fast simulation
                self.progress.emit(i)
            
            filename = f"reconstruction_model.{self.export_type.lower()}"
            if self.export_type == "Gaussian Scene":
                filename = "point_cloud.ply"
            elif self.export_type == "Mesh":
                filename = "textured_mesh.obj"
            elif self.export_type == "Images Zip":
                filename = "dataset_captures.zip"
                
            full_path = os.path.join(self.dest_path, filename)
            
            # create file stub to simulate exporting
            os.makedirs(self.dest_path, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(f"Vizhi Spatial Studio - Exported {self.export_type}\nTimestamp: {time.time()}\n")
                
            self.finished.emit(True, full_path)
        except Exception as e:
            self.finished.emit(False, str(e))


class ExportDialog(QDialog):
    def __init__(self, parent=None, default_type="Gaussian Scene"):
        super().__init__(parent)
        self.setWindowTitle("Export Workstation Model")
        self.setFixedSize(450, 240)
        self.setModal(True)
        self.default_type = default_type
        self.worker = None
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
            QLineEdit, QComboBox {
                background-color: #0D0F12;
                border: 1px solid rgba(255,255,255,0.04);
                border-radius: 6px;
                padding: 6px;
                color: #E6E6E6;
                font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #5B8CFF;
            }
            QProgressBar {
                background-color: #0D0F12;
                border: 1px solid rgba(255,255,255,0.04);
                border-radius: 4px;
                text-align: center;
                color: #E6E6E6;
                font-size: 10px;
                font-weight: bold;
                height: 16px;
            }
            QProgressBar::chunk {
                background-color: #5B8CFF;
                border-radius: 4px;
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
            QPushButton#ExportBtn {
                background-color: #5B8CFF;
                border: 1px solid rgba(255,255,255,0.04);
                color: #ffffff;
            }
            QPushButton#ExportBtn:hover {
                background-color: #6EA8FE;
                border: 1px solid rgba(255,255,255,0.08);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Export Format type
        type_layout = QVBoxLayout()
        type_lbl = QLabel("Export Format Target")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Gaussian Scene", "Point Cloud (PLY)", "Mesh (OBJ)", "Images Zip", "System Logs"])
        self.type_combo.setCurrentText(self.default_type)
        type_layout.addWidget(type_lbl)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        # Destination Path selection
        dest_layout = QVBoxLayout()
        dest_lbl = QLabel("Destination Directory")
        dest_row = QHBoxLayout()
        self.dest_input = QLineEdit(r"D:\vizhi-spatial-software\outputs")
        btn_browse = QPushButton("Browse")
        btn_browse.clicked.connect(self.browse_dest)
        dest_row.addWidget(self.dest_input)
        dest_row.addWidget(btn_browse)
        dest_layout.addWidget(dest_lbl)
        dest_layout.addLayout(dest_row)
        layout.addLayout(dest_layout)

        # Progress tracker
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        layout.addStretch()

        # Action button row
        self.btn_row = QHBoxLayout()
        self.btn_row.addStretch()
        
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.reject)
        
        self.btn_export = QPushButton("Export")
        self.btn_export.setObjectName("ExportBtn")
        self.btn_export.clicked.connect(self.start_export)
        
        self.btn_row.addWidget(self.btn_close)
        self.btn_row.addWidget(self.btn_export)
        layout.addLayout(self.btn_row)

    def browse_dest(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Destination Folder", self.dest_input.text())
        if dir_path:
            self.dest_input.setText(os.path.normpath(dir_path))

    def start_export(self):
        self.btn_export.setEnabled(False)
        self.type_combo.setEnabled(False)
        self.dest_input.setEnabled(False)
        
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        export_type = self.type_combo.currentText()
        dest_path = self.dest_input.text().strip()
        
        self.worker = ExportWorker(export_type, dest_path)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_export_finished)
        self.worker.start()

    def on_export_finished(self, success, result):
        self.btn_export.setEnabled(True)
        self.type_combo.setEnabled(True)
        self.dest_input.setEnabled(True)
        
        if success:
            NotificationManager().show_notification(f"Export completed: {os.path.basename(result)}", "success")
            self.accept()
        else:
            NotificationManager().show_notification(f"Export failed: {result}", "error")
            self.progress_bar.hide()
