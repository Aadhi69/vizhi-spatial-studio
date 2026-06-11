APP_STYLE = """
QMainWindow {
    background-color: #050B18;
}

QWidget {
    background-color: #050B18;
    color: #EAF1FF;
    font-family: Segoe UI;
    font-size: 13px;
}

QFrame {
    background: qlineargradient(
        x1:0, y1:0,
        x2:1, y2:1,
        stop:0 #091427,
        stop:1 #0B1730
    );
    border: 1px solid #13284A;
    border-radius: 18px;
}

QPushButton {
    background-color: #182D52;
    border: 1px solid #274574;
    border-radius: 14px;
    padding: 14px;
    font-weight: bold;
    color: white;
}

QPushButton:hover {
    background-color: #2558B8;
}

QLineEdit,
QTextEdit,
QListWidget,
QSpinBox {
    background-color: #081224;
    border: 1px solid #183154;
    border-radius: 12px;
    padding: 10px;
    color: white;
}

QProgressBar {
    background-color: #081224;
    border-radius: 8px;
    height: 12px;
    border: none;
}

QProgressBar::chunk {
    background-color: #2B7FFF;
    border-radius: 8px;
}

QTabWidget::pane {
    border: none;
}

QTabBar::tab {
    background: #0D1B35;
    padding: 12px 18px;
    border-radius: 10px;
    margin-right: 6px;
}

QTabBar::tab:selected {
    background: #2B7FFF;
}

QSplitter::handle {
    background: #12213D;
}

QScrollBar:vertical {
    background: #081224;
    width: 10px;
}

QScrollBar::handle:vertical {
    background: #24406B;
    border-radius: 5px;
}
"""