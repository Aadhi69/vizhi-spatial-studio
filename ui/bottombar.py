from PyQt6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QTextEdit
)

from PyQt6.QtCore import Qt


class BottomDock(QDockWidget):

    def __init__(self):
        super().__init__("Console")

        self.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea
        )

        container = QWidget()
        self.setWidget(container)

        layout = QVBoxLayout(container)

        self.tabs = QTabWidget()

        self.logs = QTextEdit()
        self.logs.setReadOnly(True)

        self.tasks = QTextEdit()
        self.notifications = QTextEdit()

        self.tabs.addTab(self.logs, "System Logs")
        self.tabs.addTab(self.tasks, "Tasks")
        self.tabs.addTab(self.notifications, "Notifications")

        layout.addWidget(self.tabs)