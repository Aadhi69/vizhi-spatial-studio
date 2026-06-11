from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout


class MetricCard(QFrame):

    def __init__(self, title, value):
        super().__init__()

        self.setMinimumHeight(90)

        layout = QVBoxLayout(self)

        self.title = QLabel(title)
        self.title.setStyleSheet("""
            color:#8EA9D6;
            font-size:14px;
        """)

        self.value = QLabel(value)
        self.value.setStyleSheet("""
            font-size:32px;
            font-weight:bold;
            color:white;
        """)

        layout.addWidget(self.title)
        layout.addWidget(self.value)