from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFrame, QApplication
from PyQt6.QtCore import Qt

class ErrorDialog(QDialog):
    def __init__(self, message, traceback_text="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("System Exception Raised")
        self.setFixedSize(500, 200) # Compact height on start
        self.setModal(True)
        self.message = message
        self.traceback_text = traceback_text
        self.details_visible = False
        self.build_ui()

    def build_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #111214;
                border: 1px solid rgba(255,255,255,0.04);
            }
            QLabel {
                font-size: 12px;
                color: #D95C5C; /* Error red */
            }
            QLabel#Title {
                font-size: 13px;
                font-weight: bold;
                color: #D95C5C; /* Alert red */
            }
            QTextEdit {
                background-color: #0D0F12;
                border: 1px solid rgba(255,255,255,0.04);
                border-radius: 6px;
                font-family: "JetBrains Mono", "Consolas", monospace;
                font-size: 11px;
                color: #E6E6E6;
                padding: 6px;
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

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(12)

        # Title
        title_lbl = QLabel("Critical Error Encountered")
        title_lbl.setObjectName("Title")
        self.main_layout.addWidget(title_lbl)

        # Message
        self.msg_lbl = QLabel(self.message)
        self.msg_lbl.setWordWrap(True)
        self.main_layout.addWidget(self.msg_lbl)

        sep = QFrame()
        sep.setObjectName("Separator")
        self.main_layout.addWidget(sep)

        # Details text (hidden by default)
        self.details_text = QTextEdit(self.traceback_text)
        self.details_text.setReadOnly(True)
        self.details_text.hide()
        self.main_layout.addWidget(self.details_text)

        # Buttons
        self.btn_row = QHBoxLayout()
        
        self.btn_details = QPushButton("Show Details")
        self.btn_details.clicked.connect(self.toggle_details)
        self.btn_row.addWidget(self.btn_details)
        
        self.btn_copy = QPushButton("Copy Traceback")
        self.btn_copy.clicked.connect(self.copy_traceback)
        self.btn_copy.setEnabled(bool(self.traceback_text))
        self.btn_row.addWidget(self.btn_copy)
        
        self.btn_row.addStretch()
        
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        self.btn_row.addWidget(btn_ok)
        
        self.main_layout.addLayout(self.btn_row)

    def toggle_details(self):
        if self.details_visible:
            self.details_text.hide()
            self.btn_details.setText("Show Details")
            self.setFixedSize(500, 200)
            self.details_visible = False
        else:
            self.details_text.show()
            self.btn_details.setText("Hide Details")
            self.setFixedSize(500, 400)
            self.details_visible = True

    def copy_traceback(self):
        if self.traceback_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(f"Error: {self.message}\n\nTraceback:\n{self.traceback_text}")
            self.btn_copy.setText("Copied!")
            # reset text after a short delay
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1500, lambda: self.btn_copy.setText("Copy Traceback"))
