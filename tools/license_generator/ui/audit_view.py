from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QPushButton, QHBoxLayout, QLabel, QLineEdit,
                               QComboBox, QFrame)
from PySide6.QtCore import Qt, QTimer
from core.firebase_manager import OnlineManager
from .styles import (TABLE_STYLE, BUTTON_SECONDARY_STYLE, INPUT_STYLE, COMBOBOX_STYLE,
                     CARD_BLUE, CARD_GREEN, CARD_ORANGE, CARD_PURPLE) # reuse card styles

class AuditLogView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = OnlineManager()
        self.logs = []
        self.filtered_logs = []
        self.stats_labels = {}
        self._setup_ui()
        
    def showEvent(self, event):
        self.refresh_data()
        super().showEvent(event)
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # --- Header ---
        header = QHBoxLayout()
        
        # Title
        title_box = QVBoxLayout()
        t = QLabel("System Audit Logs")
        t.setStyleSheet("font-size: 24px; font-weight: bold; color: #e2e8f0;")
        sub = QLabel("Monitor system events and security")
        sub.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(t)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        
        header.addStretch()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search logs...")
        self.search_input.setFixedWidth(250)
        self.search_input.setStyleSheet(INPUT_STYLE)
        self.search_input.textChanged.connect(self._apply_filter)
        header.addWidget(self.search_input)
        
        # Status Filter
        self.status_combo = QComboBox()
        self.status_combo.addItem("All Status")
        self.status_combo.addItem("Success")
        self.status_combo.addItem("Failed")
        self.status_combo.addItem("Error")
        self.status_combo.setFixedWidth(120)
        self.status_combo.setStyleSheet(COMBOBOX_STYLE)
        self.status_combo.currentIndexChanged.connect(self._apply_filter)
        header.addWidget(self.status_combo)

        # Refresh
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        refresh_btn.setStyleSheet(BUTTON_SECONDARY_STYLE)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # --- Stats Bar ---
        self._create_stats_bar(layout)
        
        # --- Table ---
        self.table = QTableWidget()
        cols = ["Time", "Event", "Email", "Status", "IP", "HWID", "Reason/Details"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.table)
        
    def _create_stats_bar(self, layout):
        container = QHBoxLayout()
        container.setSpacing(15)
        
        def _card(key, title, icon, color_style):
            frame = QFrame()
            frame.setStyleSheet(color_style)
            frame.setFixedHeight(100)
            
            # Use QVBoxLayout directly in frame? Or generic styles?
            # Styles define QFrame background. QLabel bg handled by styles.py fix.
            
            l = QHBoxLayout(frame)
            l.setContentsMargins(20, 15, 20, 15)
            
            v = QVBoxLayout()
            # Title
            t = QLabel(title)
            t.setStyleSheet("color: #e2e8f0; font-weight: bold; font-size: 11px; background-color: transparent;")
            # Value
            val = QLabel("0")
            val.setStyleSheet("font-size: 24px; font-weight: bold; color: white; background-color: transparent;")
            self.stats_labels[key] = val
            v.addWidget(t)
            v.addWidget(val)
            l.addLayout(v)
            l.addStretch()
            
            # Icon
            ic = QLabel(icon)
            ic.setStyleSheet("font-size: 36px; background: transparent;")
            l.addWidget(ic)
            return frame
            
        container.addWidget(_card("TOTAL", "TOTAL EVENTS", "📋", CARD_BLUE)) # Blue
        container.addWidget(_card("SUCCESS", "SUCCESSFUL", "✅", CARD_GREEN)) # Green 
        container.addWidget(_card("FAILED", "FAILED / ERROR", "⚠️", CARD_ORANGE)) # Orange/Red
        
        layout.addLayout(container)

    def refresh_data(self):
        # Fetching more logs since we have filtering now
        self.logs = self.manager.get_audit_logs(limit=200) 
        self._apply_filter()
        
    def _apply_filter(self):
        search_txt = self.search_input.text().lower().strip()
        status_filter = self.status_combo.currentText().lower()
        if "all" in status_filter: status_filter = None
        
        self.filtered_logs = []
        
        for log in self.logs:
            # Check Status
            st = str(log.get('status', '')).lower()
            if status_filter:
                if status_filter not in st:
                    continue
            
            # Check Search
            if search_txt:
                blob = (f"{log.get('event','')} {log.get('email','')} "
                        f"{st} {log.get('ip','')} {log.get('hwid','')}").lower()
                if search_txt not in blob:
                    continue
                    
            self.filtered_logs.append(log)
            
        self._populate_table(self.filtered_logs)
        self._update_stats()

    def _update_stats(self):
        total = len(self.filtered_logs)
        success = 0
        failed = 0
        
        for log in self.filtered_logs:
            st = str(log.get('status', '')).lower()
            if 'success' in st or 'active' in st:
                success += 1
            else:
                failed += 1
                
        if "TOTAL" in self.stats_labels: self.stats_labels["TOTAL"].setText(str(total))
        if "SUCCESS" in self.stats_labels: self.stats_labels["SUCCESS"].setText(str(success))
        if "FAILED" in self.stats_labels: self.stats_labels["FAILED"].setText(str(failed))

    def _populate_table(self, logs):
        self.table.setRowCount(0)
        self.table.setRowCount(len(logs))
        
        for r, log in enumerate(logs):
            # timestamp
            ts = log.get('timestamp')
            ts_str = str(ts)
            if hasattr(ts, 'strftime'):
                ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
            elif hasattr(ts, 'isoformat'): # Firestore TS object
                ts_str = ts.isoformat()
            
            self.table.setItem(r, 0, QTableWidgetItem(ts_str))
            
            # event
            self.table.setItem(r, 1, QTableWidgetItem(str(log.get('event', '-'))))
            
            # email
            self.table.setItem(r, 2, QTableWidgetItem(str(log.get('email', '-'))))
            
            # status
            status = str(log.get('status', '-'))
            item = QTableWidgetItem(status.upper())
            if status == 'success':
                item.setForeground(Qt.green)
            else:
                item.setForeground(Qt.red)
            self.table.setItem(r, 3, item)
            
            # ip
            self.table.setItem(r, 4, QTableWidgetItem(str(log.get('ip', '-'))))
            
            # hwid
            self.table.setItem(r, 5, QTableWidgetItem(str(log.get('hwid', '-')[:15] + '...')))
            
            # reason / details
            reason = log.get('reason') or log.get('license_type', '')
            if not reason and status == 'active': reason = "Licensed Login"
            self.table.setItem(r, 6, QTableWidgetItem(str(reason)))
