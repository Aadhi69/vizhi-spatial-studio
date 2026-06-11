import sys
import platform
import shutil
import os
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout, QFrame
from PyQt6.QtCore import Qt

class SystemInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("System Information")
        self.setFixedSize(450, 320)
        self.setModal(True)
        self.build_ui()

    def build_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #111214;
                border: 1px solid rgba(255,255,255,0.04);
            }
            QLabel {
                font-size: 12px;
                color: #E6E6E6;
            }
            QLabel#Title {
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            QLabel#Header {
                color: #6F7682;
                font-weight: bold;
                font-size: 10px;
                letter-spacing: 1px;
                text-transform: uppercase;
            }
            QFrame#Separator {
                background-color: rgba(255,255,255,0.04);
                max-height: 1px;
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
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title
        title_lbl = QLabel("Workstation Diagnostics")
        title_lbl.setObjectName("Title")
        layout.addWidget(title_lbl)

        sep = QFrame()
        sep.setObjectName("Separator")
        layout.addWidget(sep)

        # Grid system details
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setContentsMargins(0, 5, 0, 5)

        # Gather dynamic statistics from core.gpu_monitor
        from core.gpu_monitor import get_cpu_name, get_ram_info, get_gpu_info, get_cuda_version, get_os_version
        
        gpu_info = get_gpu_info()[0]
        gpu_name = gpu_info["name"]
        vram_total = f"{gpu_info['vram_total']:.1f} GB" if gpu_info["vram_total"] > 0 else "N/A"
        
        ram_total, ram_used, ram_pct = get_ram_info()
        ram_str = f"{ram_total:.1f} GB Total"
        
        torch_ver = "Not Installed"
        try:
            import torch
            torch_ver = torch.__version__
        except Exception:
            pass
            
        cuda_ver = get_cuda_version()
        cuda_avail = f"Yes (CUDA {cuda_ver})" if cuda_ver != "N/A" else "No"

        cpu_name = get_cpu_name()
        os_ver = get_os_version()
        
        # Memory Check (shutil or fallback)
        disk_total = "N/A"
        try:
            total, used, free = shutil.disk_usage("D:\\")
            disk_total = f"{total / (1024**3):.1f} GB Total"
        except Exception:
            try:
                total, used, free = shutil.disk_usage("C:\\")
                disk_total = f"{total / (1024**3):.1f} GB Total"
            except Exception:
                pass

        diagnostics = [
            ("Operating System", os_ver),
            ("Processor", cpu_name),
            ("System RAM", ram_str),
            ("GPU Adapter", gpu_name),
            ("Dedicated VRAM", vram_total),
            ("Disk Storage", disk_total),
            ("Python Version", sys.version.split(" ")[0]),
            ("PyTorch Version", torch_ver),
            ("CUDA Ingestion Toolkit", cuda_avail)
        ]

        for idx, (label, val) in enumerate(diagnostics):
            lbl_widget = QLabel(label)
            lbl_widget.setObjectName("Header")
            val_widget = QLabel(val)
            val_widget.setWordWrap(True)
            
            grid.addWidget(lbl_widget, idx, 0)
            grid.addWidget(val_widget, idx, 1)

        layout.addLayout(grid)
        layout.addStretch()

        # Action row
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)
