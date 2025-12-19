"""
Modern About Dialog for License Generator
"""
import sys
import os
import platform
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QGridLayout, QFrame, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from core.config import (
    APP_NAME, COMPANY_NAME, LOGO_PATH, APP_VERSION, 
    BUILD_DATE, DEVELOPER_NAME, COMPANY_SUBTITLE
)

class AboutDialog(QDialog):
    """Modern About dialog showing application information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Window setup
        self.setWindowTitle(f"About {APP_NAME}")
        self.setMinimumSize(600, 450)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Determine theme colors (Dark Modern)
        self.colors = {
            "bg_primary": "#1F2937",    # Gray 800
            "bg_secondary": "#374151",  # Gray 700
            "text_primary": "#F9FAFB",  # Gray 50
            "text_secondary": "#9CA3AF",# Gray 400
            "accent": "#3B82F6",        # Blue 500
            "accent_hover": "#2563EB",  # Blue 600
            "border": "#4B5563"         # Gray 600
        }
        
        # Apply dialog-wide stylesheet
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.colors['bg_primary']};
                color: {self.colors['text_primary']};
            }}
            QLabel {{
                color: {self.colors['text_primary']};
            }}
            QTabWidget::pane {{
                border: 1px solid {self.colors['border']};
                background-color: {self.colors['bg_primary']};
                border-radius: 6px;
                top: -1px; 
            }}
            QTabBar::tab {{
                background: {self.colors['bg_primary']};
                color: {self.colors['text_secondary']};
                border: 1px solid {self.colors['border']};
                padding: 8px 16px;
                margin-right: 4px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background: {self.colors['bg_secondary']};
                color: {self.colors['text_primary']};
                border-bottom: 2px solid {self.colors['accent']};
            }}
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                border: none;
                background: {self.colors['bg_primary']};
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.colors['border']};
                min-height: 20px;
                border-radius: 4px;
            }}
        """)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Build the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- 1. Hero Header ---
        header = QFrame()
        header.setStyleSheet(f"background-color: {self.colors['bg_secondary']}; border-bottom: 1px solid {self.colors['border']};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 24, 24, 24)
        header_layout.setSpacing(20)
        
        # Logo
        logo_label = QLabel()
        logo_label.setFixedSize(64, 64)
        
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            pixmap = QPixmap(LOGO_PATH)
            logo_label.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            # Fallback text logo if image missing
            logo_label.setText("MSA")
            logo_label.setStyleSheet(f"background-color: {self.colors['accent']}; color: white; border-radius: 8px; font-weight: bold; font-size: 18px;")
            logo_label.setAlignment(Qt.AlignCenter)
            
        header_layout.addWidget(logo_label)
        
        # App Info (Name & Version)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        app_title = QLabel(APP_NAME)
        app_title.setStyleSheet("font-size: 24px; font-weight: bold; font-family: 'Segoe UI', sans-serif;")
        info_layout.addWidget(app_title)
        
        version_container = QHBoxLayout()
        version_container.setSpacing(8)
        
        ver_badge = QLabel(f"v{APP_VERSION}")
        ver_badge.setStyleSheet(f"""
            background-color: {self.colors['accent']}; 
            color: white; 
            padding: 2px 8px; 
            border-radius: 4px; 
            font-weight: bold;
            font-size: 11px;
        """)
        version_container.addWidget(ver_badge)
        
        build_info = QLabel(f"Build Date • {BUILD_DATE}")
        build_info.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 11px;")
        version_container.addWidget(build_info)
        
        version_container.addStretch()
        info_layout.addLayout(version_container)
        
        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        
        main_layout.addWidget(header)
        
        # --- 2. Tabs Content ---
        content_wrapper = QVBoxLayout()
        content_wrapper.setContentsMargins(20, 20, 20, 20)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_general_tab(), "General")
        self.tabs.addTab(self._create_system_tab(), "System")
        self.tabs.addTab(self._create_terms_tab(), "Terms of Use")
        
        content_wrapper.addWidget(self.tabs)
        main_layout.addLayout(content_wrapper)
        
        # --- 3. Footer Actions ---
        footer = QHBoxLayout()
        footer.setContentsMargins(20, 0, 20, 20)
        footer.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setMinimumWidth(100)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['bg_secondary']};
                color: {self.colors['text_primary']};
                border: 1px solid {self.colors['border']};
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {self.colors['border']};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        footer.addWidget(close_btn)
        
        main_layout.addLayout(footer)

    def _create_general_tab(self):
        """Create 'General' tab content."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Description
        desc_label = QLabel(
            f"<b>{COMPANY_NAME}</b> - {COMPANY_SUBTITLE}<br><br>"
            "Administrator tool for managing MSA software licenses, customer accounts, and invoices. "
            "Designed for streamlining the activation and renewal process."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"font-size: 13px; color: {self.colors['text_primary']}; line-height: 1.4;")
        layout.addWidget(desc_label)
        
        # Key Features Grid
        features_frame = QFrame()
        features_frame.setStyleSheet(f"background-color: {self.colors['bg_secondary']}; border-radius: 8px;")
        f_layout = QGridLayout(features_frame)
        f_layout.setContentsMargins(15, 15, 15, 15)
        f_layout.setSpacing(10)
        
        features = [
            ("🔐", "Cloud Licensing"),
            ("👥", "Customer CRM"),
            ("💰", "Invoice Generation"),
            ("📊", "Audit Logging"),
        ]
        
        for i, (icon, text) in enumerate(features):
            row, col = divmod(i, 2)
            lbl = QLabel(f"{icon}  {text}")
            lbl.setStyleSheet("font-size: 12px; font-weight: 500;")
            f_layout.addWidget(lbl, row, col)
            
        layout.addWidget(features_frame)
        layout.addStretch()
        
        # Copyright
        copyright_lbl = QLabel(f"© {datetime.now().year} {DEVELOPER_NAME}. All rights reserved.")
        copyright_lbl.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 11px;")
        copyright_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright_lbl)
        
        return tab

    def _create_system_tab(self):
        """Create 'System' tab content."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        main_form = QVBoxLayout(content)
        main_form.setSpacing(24)

        from PySide6 import __version__ as pyside_version

        # Helper to create a section
        def create_section(title, items):
            section = QWidget()
            sec_layout = QVBoxLayout(section)
            sec_layout.setSpacing(12)
            sec_layout.setContentsMargins(0, 0, 0, 0)
            
            header = QLabel(title)
            header.setStyleSheet(f"color: {self.colors['accent']}; font-weight: bold; font-size: 13px; border-bottom: 2px solid {self.colors['bg_secondary']}; padding-bottom: 4px;")
            sec_layout.addWidget(header)
            
            grid = QGridLayout()
            grid.setColumnStretch(1, 1)
            grid.setSpacing(10)
            
            for i, (key, value) in enumerate(items):
                k_lbl = QLabel(key)
                k_lbl.setStyleSheet(f"color: {self.colors['text_secondary']}; font-weight: 500;")
                v_lbl = QLabel(value)
                v_lbl.setStyleSheet(f"color: {self.colors['text_primary']}; font-family: 'Consolas', monospace;")
                v_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
                grid.addWidget(k_lbl, i, 0)
                grid.addWidget(v_lbl, i, 1)
                
            sec_layout.addLayout(grid)
            return section

        # 1. Application Details
        app_items = [
            ("Version", f"{APP_VERSION}"),
            ("Build Date", f"{BUILD_DATE}"),
        ]
        
        # 2. Runtime Environment
        runtime_items = [
             ("Python", sys.version.split()[0]),
             ("Qt Framework", f"PySide6 {pyside_version}"),
             ("Platform", f"{platform.system()} {platform.release()}"),
        ]
        
        # 3. Hardware Info
        hw_items = [
             ("Architecture", platform.machine()),
             ("Processor", platform.processor() or "Unknown"),
             ("Hostname", platform.node())
        ]
        
        main_form.addWidget(create_section("Application", app_items))
        main_form.addWidget(create_section("Runtime Environment", runtime_items))
        main_form.addWidget(create_section("Hardware", hw_items))
        main_form.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)
        return tab

    def _create_terms_tab(self):
        """Create 'Terms of Use' tab content."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        license_header = QLabel("Terms of Use")
        license_header.setStyleSheet(f"color: {self.colors['text_secondary']}; font-weight: bold;")
        layout.addWidget(license_header)

        license_text = QLabel()
        license_text.setWordWrap(True)
        license_text.setStyleSheet(f"font-family: 'Consolas', monospace; font-size: 11px; color: {self.colors['text_primary']};")
        
        license_text.setText(
            f"Copyright (c) {datetime.now().year} {DEVELOPER_NAME}\n\n"
            "This software is protected by copyright laws and international treaties. "
            "Unauthorized reproduction or distribution of this program, or any portion "
            "of it, may result in severe civil and criminal penalties.\n\n"
            "THIS SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR "
            "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, "
            "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE "
            "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER "
            "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, "
            "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE "
            "SOFTWARE."
        )
        
        scroll = QScrollArea()
        scroll.setWidget(license_text)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        return tab
