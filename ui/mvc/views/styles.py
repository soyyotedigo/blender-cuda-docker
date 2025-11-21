# --- Estilos CSS (QSS) para Tema Oscuro ---
DARK_STYLESHEET = """
QMainWindow {
    background-color: #1e1e1e;
}
QWidget {
    background-color: #1e1e1e;
    color: #f0f0f0;
    font-family: 'Segoe UI', 'Roboto', sans-serif;
    font-size: 14px;
}
QGroupBox {
    border: 1px solid #3d3d3d;
    border-radius: 5px;
    margin-top: 1.5em;
    font-weight: bold;
    color: #4CAF50;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px 0 3px;
}
QLineEdit, QComboBox {
    background-color: #2d2d2d;
    border: 1px solid #3d3d3d;
    border-radius: 3px;
    padding: 5px;
    color: #ffffff;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #4CAF50;
}
QPushButton {
    background-color: #0D47A1;
    color: white;
    border: none;
    padding: 8px 15px;
    border-radius: 4px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #1565C0;
}
QPushButton:pressed {
    background-color: #0D47A1;
}
QPushButton#rentButton {
    background-color: #2E7D32;
    font-size: 16px;
    padding: 10px;
}
QPushButton#rentButton:hover {
    background-color: #388E3C;
}
QTableWidget {
    background-color: #252526;
    gridline-color: #3d3d3d;
    border: 1px solid #3d3d3d;
}
QTableWidget::item:selected {
    background-color: #0D47A1;
}
QHeaderView::section {
    background-color: #333333;
    padding: 5px;
    border: 1px solid #3d3d3d;
    font-weight: bold;
}
QTextEdit {
    background-color: #121212;
    color: #00ff00;
    font-family: 'Consolas', 'Courier New', monospace;
    border: 1px solid #3d3d3d;
}
QProgressBar {
    border: 1px solid #3d3d3d;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #4CAF50;
}
"""
