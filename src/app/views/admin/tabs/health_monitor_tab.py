
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, 
    QFrame, QGridLayout, QScrollArea, QGroupBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

from utils.language_manager import language_manager

class MetricCard(QFrame):
    def __init__(self, title, icon, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        self.icon_lbl = QLabel(icon)
        self.icon_lbl.setFont(QFont("Segoe UI Emoji", 16))
        header.addWidget(self.icon_lbl)
        
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("font-weight: bold;") 
        # Color set in update_theme
        header.addWidget(self.title_lbl)
        header.addStretch()
        layout.addLayout(header)
        
        # Main Value
        self.value_lbl = QLabel("--")
        self.value_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_lbl)
        
        # Detail/Subtext
        self.detail_lbl = QLabel("")
        self.detail_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.detail_lbl)
        
    def set_value(self, value, detail=""):
        self.value_lbl.setText(str(value))
        self.detail_lbl.setText(detail)

    def update_theme(self, theme_name):
        if theme_name == 'dark':
            bg = "#374151"
            border = "#4B5563"
            text_main = "white"
            text_sub = "#9CA3AF"
        else:
            bg = "white"
            border = "#E5E7EB"
            text_main = "#111827"
            text_sub = "#6B7280"
            
        self.setStyleSheet(f"""
            MetricCard {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
        """)
        self.title_lbl.setStyleSheet(f"color: {text_sub}; font-weight: bold; border: none; background: transparent;")
        self.value_lbl.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {text_main}; border: none; background: transparent;")
        self.detail_lbl.setStyleSheet(f"color: {text_sub}; font-size: 12px; border: none; background: transparent;")
        self.icon_lbl.setStyleSheet("border: none; background: transparent;")

class ResourceGauge(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        layout = QVBoxLayout(self)
        
        self.progress = QProgressBar()
        # Initial style set in update_theme
        layout.addWidget(self.progress)
        
        self.detail_lbl = QLabel("")
        self.detail_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.detail_lbl)
        
        self.current_percent = 0
        
    def set_usage(self, percent, detail_text=""):
        self.current_percent = percent
        self.progress.setValue(int(percent))
        self.detail_lbl.setText(detail_text)
        self._update_color()

    def update_theme(self, theme_name):
        self.current_theme = theme_name
        if theme_name == 'dark':
             self.text_color = "white"
             self.border_color = "#4B5563"
             self.track_color = "#1F2937"
        else:
             self.text_color = "#1F2937"
             self.border_color = "#E5E7EB"
             self.track_color = "#F3F4F6"
             
        self.setStyleSheet(f"QGroupBox {{ color: {self.text_color}; font-weight: bold; }}")
        self.detail_lbl.setStyleSheet(f"color: {self.text_color}; border: none;")
        self._update_color() # Re-apply progress bar style with new border/track
        
    def _update_color(self):
        # Dynamic color based on percent + theme
        percent = self.current_percent
        
        # Glowing Gradients
        if percent < 60:
            # Green Glow
            bg_gradient = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #34D399, stop:1 #10B981)" 
        elif percent < 85:
            # Orange Glow
            bg_gradient = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FBBF24, stop:1 #F59E0B)"
        else:
            # Red Glow
            bg_gradient = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F87171, stop:1 #EF4444)"
            
        border = getattr(self, 'border_color', '#E5E7EB')
        track = getattr(self, 'track_color', 'white')
            
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {border};
                border-radius: 5px;
                text-align: center;
                height: 25px;
                background-color: {track};
                color: {self.text_color if hasattr(self, 'text_color') else 'black'}; 
            }}
            QProgressBar::chunk {{
                background-color: {bg_gradient};
            }}
        """)

class HealthMonitorTab(QWidget):
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.monitor = container.system_monitor_service
        self.lm = language_manager
        
        self._setup_ui()
        
        # Theme
        if hasattr(self.container, 'theme_controller'):
             self.container.theme_controller.theme_changed.connect(self.update_theme)
             self.update_theme(self.container.theme_controller.current_theme)
        else:
             self.update_theme('dark')

        # Refresh Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_stats)
        # Timer started in showEvent

    def update_theme(self, theme_name):
        # Update cards
        for card in [self.uptime_card, self.db_status_card, self.latency_card, self.system_card]:
             card.update_theme(theme_name)
             
        # Update gauges
        for gauge in [self.mem_gauge, self.disk_gauge]:
             gauge.update_theme(theme_name)
             
        # Update Labels
        if theme_name == 'dark':
            text_color = "white"
        else:
            text_color = "#1F2937"
            
        self.os_lbl.setStyleSheet(f"color: {text_color};")
        self.python_lbl.setStyleSheet(f"color: {text_color};")
        self.db_path_lbl.setStyleSheet(f"color: {text_color};")
        
        # Also update labels inside the layout if possible or set stylesheet on self
        # Be careful not to override specifics, but setting color on self propagates usually
        self.setStyleSheet(f"QLabel {{ color: {text_color}; }}")


    def showEvent(self, event):
        super().showEvent(event)
        self._update_stats()
        if not self.timer.isActive():
            self.timer.start(5000)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.timer.stop()
        
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        
        # 1. System Info Cards
        info_grid = QGridLayout()
        
        self.uptime_card = MetricCard(self.lm.get("Health.card_uptime", "Uptime"), "⏱️")
        self.db_status_card = MetricCard(self.lm.get("Health.card_db_status", "DB Status"), "🗄️")
        self.latency_card = MetricCard(self.lm.get("Health.card_db_latency", "DB Latency"), "⚡")
        self.system_card = MetricCard(self.lm.get("Health.card_system", "System"), "💻")
        
        info_grid.addWidget(self.uptime_card, 0, 0)
        info_grid.addWidget(self.db_status_card, 0, 1)
        info_grid.addWidget(self.latency_card, 0, 2)
        info_grid.addWidget(self.system_card, 0, 3)
        
        layout.addLayout(info_grid)
        
        # 2. Resources
        res_group = QGroupBox(self.lm.get("Health.group_resources", "Resource Usage"))
        res_layout = QHBoxLayout(res_group)
        
        self.mem_gauge = ResourceGauge(self.lm.get("Health.gauge_memory", "Memory Usage"))
        res_layout.addWidget(self.mem_gauge)
        
        self.disk_gauge = ResourceGauge(self.lm.get("Health.gauge_disk", "Disk Usage"))
        res_layout.addWidget(self.disk_gauge)
        
        layout.addWidget(res_group)
        
        # 3. Environment Info
        env_group = QGroupBox(self.lm.get("Health.group_env", "Environment Details"))
        env_layout = QGridLayout(env_group)
        
        self.os_lbl = QLabel()
        self.python_lbl = QLabel()
        self.db_path_lbl = QLabel()
        
        env_layout.addWidget(QLabel(self.lm.get("Health.label_os", "OS Version:")), 0, 0)
        env_layout.addWidget(self.os_lbl, 0, 1)
        
        env_layout.addWidget(QLabel(self.lm.get("Health.label_python", "Python Version:")), 1, 0)
        env_layout.addWidget(self.python_lbl, 1, 1)
        
        env_layout.addWidget(QLabel(self.lm.get("Health.label_db_path", "Database Path:")), 2, 0)
        env_layout.addWidget(self.db_path_lbl, 2, 1)
        
        layout.addWidget(env_group)
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
    def _update_stats(self):
        stats = self.monitor.get_system_stats()
        
        # Uptime
        self.uptime_card.set_value(
            f"{stats['uptime']['days']}d {stats['uptime']['hours']}h",
            f"{stats['uptime']['minutes']}m {stats['uptime']['seconds']}s"
        )
        
        # DB Status
        db_stat = stats['database']
        self.db_status_card.set_value(db_stat['status'], f"{db_stat['size_mb']} MB")
        
        # Color code DB status
        if db_stat['status'] == 'Connected':
            self.db_status_card.value_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #10B981;")
        else:
            self.db_status_card.value_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #EF4444;")
            
        self.latency_card.set_value(f"{db_stat['latency_ms']}ms")
        
        # System
        sys_info = stats['system']
        self.system_card.set_value(sys_info['system'], sys_info['release'])
        
        # Memory
        mem = stats['memory']
        # Rough percentage estimate (assuming 16GB max for simple gauge visualization, or just raw MB)
        # Since we can't easily get Total RAM without psutil, we'll just show usage relative to a high baseline or just 0-100 if we knew total.
        # Without total, a gauge is misleading if it's percentage based. 
        # But we can assume standard usage ranges.
        # Let's just update the text primarily.
        
        # For gauge, we might not have percentage without psutil.
        # So we'll disable the percentage bar logic or fake it if we can't get total.
        # ACTUALLY, usually we can get total memory from sysconf or similar but it's platform dependent.
        # Let's just stick to showing values.
        
        self.mem_gauge.progress.setVisible(False) # Hide bar if no percentage
        self.mem_gauge.detail_lbl.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.mem_gauge.detail_lbl.setText(self.lm.get("Health.text_mb_used", "{mb} MB Used").format(mb=mem['used_mb']))
        
        # Disk
        disk = stats['disk']
        self.disk_gauge.set_usage(disk['percent'], f"{disk['used_gb']} GB / {disk['total_gb']} GB")
        
        # Env Info
        self.os_lbl.setText(f"{sys_info['system']} {sys_info['release']} ({sys_info['version']})")
        self.python_lbl.setText(sys_info['python_version'])
        self.db_path_lbl.setText(str(db_stat['path']))
