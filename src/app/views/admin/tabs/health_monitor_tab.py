
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
        self.setStyleSheet("""
            MetricCard {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 16))
        header.addWidget(icon_lbl)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #6B7280; font-weight: bold;")
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)
        
        # Main Value
        self.value_lbl = QLabel("--")
        self.value_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #111827;")
        self.value_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_lbl)
        
        # Detail/Subtext
        self.detail_lbl = QLabel("")
        self.detail_lbl.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        self.detail_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.detail_lbl)

    def set_value(self, value, detail=""):
        self.value_lbl.setText(str(value))
        self.detail_lbl.setText(detail)

class ResourceGauge(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        layout = QVBoxLayout(self)
        
        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #E5E7EB;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #3B82F6;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress)
        
        self.detail_lbl = QLabel("")
        self.detail_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.detail_lbl)
        
    def set_usage(self, percent, detail_text=""):
        self.progress.setValue(int(percent))
        self.detail_lbl.setText(detail_text)
        
        # Dynamic color
        if percent < 60:
            color = "#10B981" # Green
        elif percent < 85:
            color = "#F59E0B" # Orange
        else:
            color = "#EF4444" # Red
            
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #E5E7EB;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 5px;
            }}
        """)

class HealthMonitorTab(QWidget):
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.monitor = container.system_monitor_service
        self.lm = language_manager
        
        self._setup_ui()
        
        # Refresh Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_stats)
        # Timer started in showEvent

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
