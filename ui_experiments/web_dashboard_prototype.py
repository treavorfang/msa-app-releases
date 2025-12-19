
import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Qt

class WebDashboardWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MSA Web Dashboard")
        self.resize(1200, 800)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Web View
        self.webview = QWebEngineView()
        self.webview.setStyleSheet("background: #111827;")
        
        # Load HTML
        html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "dashboard_theme.html"))
        self.webview.setUrl(QUrl.fromLocalFile(html_path))
        
        layout.addWidget(self.webview)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WebDashboardWindow()
    window.show()
    sys.exit(app.exec())
