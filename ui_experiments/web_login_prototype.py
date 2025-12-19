
import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QUrl, QObject, Slot, Qt, QPoint

class WebBridge(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent

    @Slot(str, str)
    def tryLogin(self, email, password):
        print(f"Login Attempt: Email={email}, Password={'*' * len(password)}")
        # Here you would call your actual auth service
        
    @Slot()
    def closeWindow(self):
        print("Closing window...")
        if self.window:
            self.window.close()

class WebLoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MSA Web Login")
        self.resize(400, 520) # Compact size for card only
        
        # Frameless Setup
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # Full edge-to-edge
        
        # Web View
        self.webview = QWebEngineView()
        self.webview.setStyleSheet("background: transparent;")
        self.webview.page().setBackgroundColor(Qt.transparent) # Crucial for transparency
        
        # Bridge Setup
        self.channel = QWebChannel()
        self.bridge = WebBridge(self)
        self.channel.registerObject("bridge", self.bridge)
        self.webview.page().setWebChannel(self.channel)
        
        # Load HTML
        html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "login_theme.html"))
        self.webview.setUrl(QUrl.fromLocalFile(html_path))
        
        layout.addWidget(self.webview)

        # Helper for dragging
        self.old_pos = None

        # Inject QWebChannel JS
        # We need to inject the qwebchannel.js script into the page so the HTML can talk to us
        # Typically this is done by reading the JS file from Qt resource or disk and running runJavaScript
        # For this prototype, we will inject it after load.
        self.webview.loadFinished.connect(self._on_load_finished)

    def _on_load_finished(self, ok):
        if ok:
            # Inject QWebChannel JS implementation (minified usually provided by Qt, but we can use a simple version or path)
            # PRO TIP: Qt WebEngine doesn't automatically provide qwebchannel.js in the context.
            # We need to load it. 
            pass 
            # Note: For a robust app, we bundled qwebchannel.js. 
            # For this quick prototype, the HTML might fail to call 'bridge' without the JS library.
            # Let's simple use window.pyObj approach involves setup.
            
            # Let's try to inject the necessary JS boilerplate to bind 'bridge'
            js = """
            new QWebChannel(qt.webChannelTransport, function(channel) {
                window.bridge = channel.objects.bridge;
            });
            """
            # We need qwebchannel.js first. 
            # A common trick is to supply it from a known URL or file.
            # For this MVP, let's assume the user has the file or we write it.
            
    # --- Drag Logic ---
    # Intercepting mouse events on QWebEngineView is hard because the browser engine eats them.
    # Usually we rely on a "-webkit-app-region: drag" CSS property for Electron, but Qt doesn't support that OOB.
    # Workaround: Put a transparent QWidget on top? No, that blocks clicks.
    # Workaround: Use a native title bar or accept that dragging might be tricky in this prototype.
    # OR: We can just let the user use the OS way if available, or just implement a simple mouse hook on the container edge.
    
    # We'll skip complex drag logic for this specific MVP step to focus on the Visuals.

if __name__ == "__main__":
    # Fix for qwebchannel.js:
    # We will write a minimal qwebchannel.js to the same folder for the HTML to load
    
    app = QApplication(sys.argv)
    window = WebLoginWindow()
    window.show()
    sys.exit(app.exec())
