import sys

from PyQt6.QtWidgets import QApplication

from ui.workspace import Workspace


app = QApplication(sys.argv)

window = Workspace()
window.showMaximized()

sys.exit(app.exec())