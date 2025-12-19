"""
UpdateDialog - UI for checking and downloading updates.
"""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QTextEdit, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from utils.language_manager import language_manager
from services.update_service import UpdateService

class UpdateDialog(QDialog):
    def __init__(self, update_info, parent=None):
        super().__init__(parent)
        self.lm = language_manager
        self.update_info = update_info
        self.update_service = UpdateService()
        self.download_thread = None
        
        self.setWindowTitle(self.lm.get("About.update_dialog_title", "Update Available"))
        self.setMinimumSize(500, 400)
        
        self.colors = {
            "bg_primary": "#1F2937",    # Gray 800
            "bg_secondary": "#374151",  # Gray 700
            "text_primary": "#F9FAFB",  # Gray 50
            "text_secondary": "#9CA3AF",# Gray 400
            "accent": "#3B82F6",        # Blue 500
            "accent_hover": "#2563EB",  # Blue 600
            "border": "#4B5563"         # Gray 600
        }
        
        self.setStyleSheet(f"""
            QDialog {{ background-color: {self.colors['bg_primary']}; color: {self.colors['text_primary']}; }}
            QLabel {{ color: {self.colors['text_primary']}; }}
            QTextEdit {{ 
                background-color: {self.colors['bg_secondary']}; 
                color: {self.colors['text_primary']}; 
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                padding: 10px;
            }}
        """)
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Header
        header = QLabel(f"🚀 {self.lm.get('About.new_version_available', 'A new version is available!')}")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)
        
        # Version info
        version_lbl = QLabel(f"{self.lm.get('About.version', 'Version')}: {self.update_info['version']}")
        version_lbl.setStyleSheet(f"color: {self.colors['accent']}; font-weight: bold;")
        layout.addWidget(version_lbl)
        
        # Release notes label
        layout.addWidget(QLabel(self.lm.get("About.release_notes", "Release Notes:")))
        
        # Release notes text
        self.notes_area = QTextEdit()
        self.notes_area.setReadOnly(True)
        self.notes_area.setText(self.update_info['body'])
        layout.addWidget(self.notes_area)
        
        # Progress area (hidden initially)
        self.progress_frame = QFrame()
        self.progress_frame.setVisible(False)
        prog_layout = QVBoxLayout(self.progress_frame)
        prog_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_lbl = QLabel(self.lm.get("About.downloading", "Downloading update..."))
        prog_layout.addWidget(self.status_lbl)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {self.colors['border']};
                border-radius: 5px;
                text-align: center;
                height: 20px;
                background: {self.colors['bg_secondary']};
            }}
            QProgressBar::chunk {{
                background-color: {self.colors['accent']};
                border-radius: 4px;
            }}
        """)
        prog_layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_frame)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton(self.lm.get("Common.cancel", "Cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet(self._btn_style(False))
        
        self.update_btn = QPushButton(self.lm.get("About.update_now", "Download & Install"))
        self.update_btn.clicked.connect(self._start_download)
        self.update_btn.setStyleSheet(self._btn_style(True))
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.update_btn)
        layout.addLayout(btn_layout)

    def _btn_style(self, primary):
        bg = self.colors['accent'] if primary else self.colors['bg_secondary']
        color = "white" if primary else self.colors['text_primary']
        return f"""
            QPushButton {{
                background-color: {bg};
                color: {color};
                border: 1px solid {self.colors['border']};
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['accent_hover'] if primary else self.colors['border']};
            }}
        """

    def _start_download(self):
        url = self.update_info['url']
        if not url:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "No download link found for your OS.")
            return

        filename = url.split('/')[-1]
        self.update_btn.setEnabled(False)
        self.progress_frame.setVisible(True)
        
        self.download_thread = self.update_service.create_download_thread(url, filename)
        self.download_thread.progress.connect(self.progress_bar.setValue)
        self.download_thread.finished.connect(self._on_download_finished)
        self.download_thread.error.connect(self._on_download_error)
        self.download_thread.start()

    def _on_download_finished(self, path):
        self.status_lbl.setText(self.lm.get("About.download_complete", "Download complete! Launching installer..."))
        self.update_service.launch_installer(path)
        self.accept()

    def _on_download_error(self, error_msg):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Download Error", f"Failed to download update: {error_msg}")
        self.progress_frame.setVisible(False)
        self.update_btn.setEnabled(True)
