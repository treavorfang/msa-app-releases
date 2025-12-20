# src/app/views/dialogs/about_dialog.py
"""
Modern About Dialog - Display application information.
"""
import sys
import os
import platform
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QGridLayout, QFrame, QScrollArea,
    QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QPixmap, QIcon

from config.config import APP_NAME, COMPANY_NAME, ICON_PATHS, DEVELOPER_NAME
# Attempt to import version info, fallback to defaults
try:
    from version import (
        VERSION, FULL_VERSION, BUILD_NUMBER, BUILD_DATE,
        GIT_COMMIT, GIT_BRANCH, GIT_TAG
    )
except ImportError:
    VERSION = "1.0.2"
    FULL_VERSION = "1.0.2+dev"
    BUILD_NUMBER = 0
    BUILD_DATE = datetime.now().strftime("%Y-%m-%d")
    GIT_COMMIT = "unknown"
    GIT_BRANCH = "dev"
    GIT_TAG = "v1.0.3"

from services.update_service import UpdateService
from views.dialogs.update_dialog import UpdateDialog

from utils.language_manager import language_manager

class AboutDialog(QDialog):
    """Modern About dialog showing application information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lm = language_manager
        
        # Window setup
        self.setWindowTitle(f"{self.lm.get('Common.about', 'About')} {APP_NAME}")
        self.setMinimumSize(600, 450)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Determine theme colors (Defaulting to Dark Modern for consistency with upgrade)
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
        
        logo_path = ICON_PATHS.get('logo')
        
        if logo_path and os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
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
        
        ver_badge = QLabel(f"v{VERSION}")
        ver_badge.setStyleSheet(f"""
            background-color: {self.colors['accent']}; 
            color: white; 
            padding: 2px 8px; 
            border-radius: 4px; 
            font-weight: bold;
            font-size: 11px;
        """)
        version_container.addWidget(ver_badge)
        
        # Add version type badge (Beta/Release) based on license
        version_type_badge = self._get_version_type_badge()
        if version_type_badge:
            version_container.addWidget(version_type_badge)
        
        build_info = QLabel(f"Build {BUILD_NUMBER} • {BUILD_DATE}")
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
        self.tabs.addTab(self._create_general_tab(), self.lm.get("About.tab_general", "General"))
        self.tabs.addTab(self._create_whats_new_tab(), self.lm.get("About.tab_whatsnew", "What's New"))
        self.tabs.addTab(self._create_system_tab(), self.lm.get("About.tab_system", "System"))
        self.tabs.addTab(self._create_terms_tab(), self.lm.get("About.tab_terms", "Terms of Use"))
        self.tabs.addTab(self._create_credits_tab(), self.lm.get("About.tab_credits", "Credits"))
        self.tabs.addTab(self._create_license_tab(), self.lm.get("About.tab_license", "License"))
        
        content_wrapper.addWidget(self.tabs)
        main_layout.addLayout(content_wrapper)
        
        # --- 3. Footer Actions ---
        footer = QHBoxLayout()
        footer.setContentsMargins(20, 0, 20, 20)
        
        # Update Button
        self.update_btn = QPushButton(self.lm.get("About.check_updates", "Check for Updates"))
        self.update_btn.setCursor(Qt.PointingHandCursor)
        self.update_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['accent']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {self.colors['accent_hover']};
            }}
            QPushButton:disabled {{
                background-color: {self.colors['bg_secondary']};
                color: {self.colors['text_secondary']};
            }}
        """)
        self.update_btn.clicked.connect(self._check_for_updates)
        footer.addWidget(self.update_btn)
        
        footer.addStretch()
        
        close_btn = QPushButton(self.lm.get("Common.close", "Close"))
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

    def _check_for_updates(self):
        """Invoke update service to check for new versions."""
        self.update_btn.setEnabled(False)
        self.update_btn.setText(self.lm.get("About.checking", "Checking..."))
        
        # Use QTimer to allow UI update before blocking call (or ideally use thread)
        # For now, simple synchronous call is acceptable as request timeout is short (10s)
        # But better to use the service in a non-blocking way if possible.
        # The UpdateService.check_for_updates IS blocking. 
        # Let's use a simple delayed call to let the button redraw first.
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self._perform_check)

    def _perform_check(self):
        try:
            service = UpdateService()
            result = service.check_for_updates()
            
            if result.get("update_available"):
                # Show update dialog
                dlg = UpdateDialog(result, self)
                if dlg.exec():
                    # If update started/completed, maybe close about?
                    pass
            elif result.get("error"):
                 QMessageBox.warning(
                    self, 
                    self.lm.get("Common.error", "Error"),
                    f"{self.lm.get('About.check_failed', 'Update check failed')}: {result['error']}"
                )
            else:
                QMessageBox.information(
                    self, 
                    self.lm.get("About.up_to_date", "Up to Date"),
                    f"{self.lm.get('About.latest_version_msg', 'You are using the latest version')} ({VERSION})."
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            self.update_btn.setEnabled(True)
            self.update_btn.setText(self.lm.get("About.check_updates", "Check for Updates"))
    
    def _get_version_type_badge(self):
        """
        Determine version type based on environment and license.
        Returns QLabel with 'Beta Version' for development mode or developer licenses,
        'Release' for production.
        """
        from services.license_service import LicenseService
        from config.flags import is_development
        
        try:
            # Check if running in development mode
            in_dev_mode = is_development()
            
            service = LicenseService()
            result = service.check_online_status()
            
            if result.get('valid'):
                details = result.get('details', {})
                license_name = details.get('name', '').lower()
                
                # Check if this is a developer/beta license
                # Developer licenses typically have "developer", "dev", "beta", or "test" in the name
                is_developer_license = any(keyword in license_name for keyword in ['developer', 'dev', 'beta', 'test', 'studio tai', DEVELOPER_NAME.lower()])
                
                # Show BETA if in development mode OR using a developer license
                if in_dev_mode or is_developer_license:
                    # Beta Version badge (orange/yellow)
                    badge = QLabel("BETA")
                    badge.setStyleSheet("""
                        background-color: #F59E0B; 
                        color: white; 
                        padding: 2px 8px; 
                        border-radius: 4px; 
                        font-weight: bold;
                        font-size: 11px;
                    """)
                    tooltip = "Development Mode" if in_dev_mode else "Developer License"
                    badge.setToolTip(tooltip)
                    return badge
                else:
                    # Release badge (green)
                    badge = QLabel("RELEASE")
                    badge.setStyleSheet("""
                        background-color: #10B981; 
                        color: white; 
                        padding: 2px 8px; 
                        border-radius: 4px; 
                        font-weight: bold;
                        font-size: 11px;
                    """)
                    badge.setToolTip("Production License")
                    return badge
            else:
                # No valid license - show as Beta/Unlicensed
                badge = QLabel("UNLICENSED")
                badge.setStyleSheet("""
                    background-color: #EF4444; 
                    color: white; 
                    padding: 2px 8px; 
                    border-radius: 4px; 
                    font-weight: bold;
                    font-size: 11px;
                """)
                return badge
                
        except Exception as e:
            print(f"Error determining version type: {e}")
            return None

    def _create_general_tab(self):
        """Create 'General' tab content."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Description
        desc_label = QLabel(
            f"<b>{APP_NAME}</b> is a comprehensive management solution designed for modern "
            "repair centers and service businesses. Streamline tickets, inventory, "
            "and customer relationships in one unified platform."
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
            ("🎫", "Ticket ManagementSystem"),
            ("👥", "Customer CRM"),
            ("📦", "Inventory Control"),
            ("💰", "Financial Reporting"),
            ("📊", "Business Analytics"),
            ("🔌", "Plugin Architecture"),
        ]
        
        for i, (icon, text) in enumerate(features):
            row, col = divmod(i, 2)
            lbl = QLabel(f"{icon}  {text}")
            lbl.setStyleSheet("font-size: 12px; font-weight: 500;")
            f_layout.addWidget(lbl, row, col)
            
        layout.addWidget(features_frame)
        layout.addStretch()
        
        # Copyright
        copyright_lbl = QLabel(f"© {datetime.now().year} {COMPANY_NAME}. All rights reserved.")
        copyright_lbl.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 11px;")
        copyright_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright_lbl)
        
        return tab
    
    def _create_whats_new_tab(self):
        """Create 'What's New' tab content."""
        from config.config import CHANGELOG
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QLabel()
        content.setWordWrap(True)
        content.setOpenExternalLinks(True)
        content.setTextInteractionFlags(Qt.TextBrowserInteraction)
        
        # Build list items
        def build_list(items, tag_class, tag_text):
            if not items:
                return ""
            html_list = "<ul>"
            for item in items:
                html_list += f'<li><span class="{tag_class}">[{tag_text}]</span> {item}</li>'
            html_list += "</ul>"
            return html_list

        new_features_html = build_list(CHANGELOG.get('new_features', []), "new", "NEW")
        improvements_html = build_list(CHANGELOG.get('improvements', []), "new", "IMPROVED") # Reusing new class/style for simplicity or define improved
        bug_fixes_html = build_list(CHANGELOG.get('bug_fixes', []), "fix", "FIX")

        html = f"""
        <style>
            h3 {{ color: {self.colors['accent']}; margin-bottom: 5px; margin-top: 15px; }}
            h4 {{ color: {self.colors['text_primary']}; margin-bottom: 2px; margin-top: 10px; }}
            ul {{ margin-top: 0px; margin-bottom: 0px; }}
            li {{ font-size: 12px; margin-bottom: 4px; color: {self.colors['text_primary']}; }}
            .tag {{ font-weight: bold; color: {self.colors['text_secondary']}; font-size: 10px; }}
            .new {{ color: #10B981; font-weight: bold; }}
            .fix {{ color: #F59E0B; font-weight: bold; }}
        </style>
        
        <h3>🚀 Release {VERSION} Highlights</h3>
        <p>{CHANGELOG.get('release_highlights', '')}</p>
        
        <h4>✨ New Features</h4>
        {new_features_html}
        
        <h4>🔧 Improvements</h4>
        {improvements_html}
        
        <h4>🐛 Bug Fixes</h4>
        {bug_fixes_html}
        """
        content.setText(html)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
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
            ("Version", f"{FULL_VERSION}"),
            ("Build", f"{BUILD_NUMBER} ({BUILD_DATE})"),
            ("Commit", f"{GIT_COMMIT[:7] if GIT_COMMIT != 'unknown' else 'N/A'} ({GIT_BRANCH})"),
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

    def _create_credits_tab(self):
        """Create 'Credits' tab content."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # Using QLabel with Rich Text for credits
        credits_content = QLabel()
        credits_content.setWordWrap(True)
        credits_content.setOpenExternalLinks(True)
        credits_content.setTextInteractionFlags(Qt.TextBrowserInteraction)
        
        html = f"""
        <style>
            h3 {{ color: {self.colors['accent']}; margin-bottom: 5px; }}
            p, li {{ font-size: 12px; margin-bottom: 5px; color: {self.colors['text_primary']}; }}
            .role {{ font-weight: bold; color: {self.colors['text_secondary']}; }}
        </style>
        
        <h3>Core Development Team</h3>
        <ul>
            <li><b>{DEVELOPER_NAME}</b> - <span class="role">Lead Architecture & Design</span></li>
            <li>EventBus Pattern - <span class="role">System Architecture</span></li>
        </ul>
        
        <h3>Open Source Libraries</h3>
        <p>This software uses the following open source technologies:</p>
        <ul>
            <li><b>PySide6</b> (Qt for Python)</li>
            <li><b>Peewee ORM</b> - Database Management</li>
            <li><b>Matplotlib</b> - Data Visualization</li>
            <li><b>ReportLab</b> - PDF Generation</li>
        </ul>
        
        <h3>Special Thanks</h3>
        <p>To all the beta testers and contributors who helped shape this release.</p>
        """
        credits_content.setText(html)
        
        scroll.setWidget(credits_content)
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
        
        from datetime import datetime
        license_text.setText(
            f"Copyright (c) {datetime.now().year} {COMPANY_NAME}\n\n"
            "This software is protected by copyright laws and international treaties. "
            "Unauthorized reproduction or distribution of this program, or any portion "
            "of it, may result in severe civil and criminal penalties.\n\n"
            "THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 'AS IS' AND ANY EXPRESS OR IMPLIED WARRANTIES, "
            "INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. "
            "IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, "
            "OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; "
            "OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT "
            "(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
        )
        
        scroll = QScrollArea()
        scroll.setWidget(license_text)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        return tab

    def _create_license_tab(self):
        """Create 'License' tab content with dynamic license info."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # --- License Status Section ---
        from services.license_service import LicenseService
        service = LicenseService()
        result = service.check_online_status()
        
        if result['valid']:
            details = result.get('details', {})
            name = details.get('name', 'Unknown')
            expiry = details.get('expiry', 'Never')
            hwid = details.get('hwid', 'Unknown')
            
            # Valid Status Header
            status_container = QHBoxLayout()
            icon_lbl = QLabel("✅")
            icon_lbl.setStyleSheet("font-size: 24px;")
            
            status_title = QLabel("LICENSE ACTIVE")
            status_title.setStyleSheet(f"color: {self.colors['accent']}; font-weight: bold; font-size: 20px;")
            
            status_container.addWidget(icon_lbl)
            status_container.addWidget(status_title)
            status_container.addStretch()
            layout.addLayout(status_container)
            
            # Info Grid
            grid_frame = QFrame()
            grid_frame.setStyleSheet(f"background-color: {self.colors['bg_secondary']}; border-radius: 8px; padding: 15px;")
            grid = QGridLayout(grid_frame)
            grid.setSpacing(15)
            
            def add_row_large(row, label, value):
                l = QLabel(label)
                l.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 13px;")
                v = QLabel(value)
                v.setStyleSheet(f"color: {self.colors['text_primary']}; font-weight: bold; font-size: 14px;")
                v.setTextInteractionFlags(Qt.TextSelectableByMouse)
                grid.addWidget(l, row, 0)
                grid.addWidget(v, row, 1)

            add_row_large(0, "Licensed To", name)
            add_row_large(1, "Expiration Date", expiry)
            add_row_large(2, "Machine ID", hwid)
            
            layout.addWidget(grid_frame)
            
            # Action Buttons (e.g. Refresh)
            # btn_layout = QHBoxLayout()
            # refresh_btn = QPushButton("Refresh License")
            # refresh_btn.setFixedWidth(120)
            # btn_layout.addWidget(refresh_btn)
            # btn_layout.addStretch()
            # layout.addLayout(btn_layout)
            
        else:
            # Invalid/Missing
            status_lbl = QLabel("⚠️ NO VALID LICENSE FOUND")
            status_lbl.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 20px;")
            layout.addWidget(status_lbl)
            
            msg = QLabel(result.get('message', 'Unknown Error'))
            msg.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 14px;")
            msg.setWordWrap(True)
            layout.addWidget(msg)
            
        layout.addStretch()
        
        return tab

def show_about_dialog(parent=None):
    """Show the About dialog."""
    try:
        dialog = AboutDialog(parent)
        dialog.exec()
    except Exception as e:
        print(f"ERROR showing About Dialog: {e}")
        import traceback
        traceback.print_exc()
