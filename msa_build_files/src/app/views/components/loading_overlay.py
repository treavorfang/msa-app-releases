from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QRect, QEvent
from PySide6.QtGui import QPainter, QColor, QPen

class LoadingSpinner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(40)
        self.setFixedSize(50, 50)

    def rotate(self):
        self.angle = (self.angle + 30) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        painter.translate(w / 2, h / 2)
        painter.rotate(self.angle)
        
        pen = QPen(QColor("#2196F3"))  # Material Blue
        pen.setWidth(4)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        # Draw spinner arc
        painter.drawArc(-15, -15, 30, 30, 0, 300 * 16)

class LoadingOverlay(QWidget):
    """
    Generic loading overlay that covers its parent widget.
    Usage:
        self.overlay = LoadingOverlay(self)
        ...
        self.overlay.start("Loading data...")
        self.overlay.stop()
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False) # Block clicks
        self.setAttribute(Qt.WA_NoSystemBackground) # Allow transparency
        
        # Semi-transparent background
        self.setStyleSheet("background-color: rgba(255, 255, 255, 180);")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.spinner = LoadingSpinner()
        layout.addWidget(self.spinner)
        
        self.message_label = QLabel("Loading...")
        self.message_label.setStyleSheet("""
            QLabel {
                color: #555; 
                font-weight: bold; 
                margin-top: 10px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.message_label)
        
        self.hide()
        
        # Monitor parent resize events
        if parent:
            parent.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.parent() and event.type() == QEvent.Resize:
            self.resize(obj.size())
        return super().eventFilter(obj, event)

    def start(self, message=None):
        """Show the overlay with an optional message"""
        if message:
            self.message_label.setText(message)
        self.resize(self.parent().size())
        self.show()
        self.raise_()

    def stop(self):
        """Hide the overlay"""
        self.hide()
