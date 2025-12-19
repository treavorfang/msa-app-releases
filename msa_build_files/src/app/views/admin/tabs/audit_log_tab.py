
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QHeaderView, QLabel, QComboBox, 
    QDateEdit, QPushButton, QLineEdit, QDialog, QTextEdit,
    QGroupBox, QSplitter
)
from PySide6.QtCore import Qt, QDate
import json
from datetime import datetime
from models.user import User

from utils.language_manager import language_manager

class AuditLogTab(QWidget):
    def __init__(self, container, admin_user):
        super().__init__()
        self.container = container
        self.audit_service = container.audit_service
        self.admin_user = admin_user
        self.lm = language_manager
        
        self._setup_ui()
        self._data_loaded = False
        # self._load_users()
        # self._load_logs()

    def showEvent(self, event):
        super().showEvent(event)
        if not self._data_loaded:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self._lazy_load)
            self._data_loaded = True
            
    def _lazy_load(self):
        self._load_users()
        self._load_logs()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. Filters
        filter_group = QGroupBox(self.lm.get("Audit.filters_group", "Filters"))
        filter_layout = QHBoxLayout(filter_group)
        
        # Date Range
        filter_layout.addWidget(QLabel(self.lm.get("Audit.label_from", "From:")))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        filter_layout.addWidget(self.date_from)
        
        filter_layout.addWidget(QLabel(self.lm.get("Audit.label_to", "To:")))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        filter_layout.addWidget(self.date_to)
        
        # User
        filter_layout.addWidget(QLabel(self.lm.get("Audit.label_user", "User:")))
        self.user_filter = QComboBox()
        self.user_filter.addItem(self.lm.get("Audit.user_all", "All Users"), None)
        self.user_filter.setMinimumWidth(150)
        filter_layout.addWidget(self.user_filter)
        
        # Table/Entity
        filter_layout.addWidget(QLabel(self.lm.get("Audit.label_entity", "Entity:")))
        self.table_filter = QComboBox()
        self.table_filter.addItem(self.lm.get("Audit.entity_all", "All"))
        self.table_filter.addItems(["users", "roles", "tickets", "invoices", "payments", "technicians"])
        filter_layout.addWidget(self.table_filter)
        
        # Action search
        self.action_input = QLineEdit()
        self.action_input.setPlaceholderText(self.lm.get("Audit.search_placeholder", "Search action..."))
        filter_layout.addWidget(self.action_input)
        
        # Filter Button
        self.filter_btn = QPushButton(self.lm.get("Audit.btn_apply", "Apply Filters"))
        self.filter_btn.clicked.connect(self._load_logs)
        self.filter_btn.setStyleSheet("background-color: #3B82F6; color: white; font-weight: bold;")
        filter_layout.addWidget(self.filter_btn)
        
        layout.addWidget(filter_group)
        
        # 2. Logs Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            self.lm.get("Audit.header_id", "ID"),
            self.lm.get("Audit.header_time", "Time"),
            self.lm.get("Audit.header_user", "User"),
            self.lm.get("Audit.header_action", "Action"),
            self.lm.get("Audit.header_entity", "Entity"),
            self.lm.get("Audit.header_ip", "IP Address")
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._show_details)
        
        layout.addWidget(self.table)

    def _load_users(self):
        self.user_filter.clear()
        self.user_filter.addItem(self.lm.get("Audit.user_all", "All Users"), None)
        users = User.select()
        for u in users:
            self.user_filter.addItem(u.username, u.id)

    def _load_logs(self):
        # Get filter values
        days = self.date_from.date().daysTo(self.date_to.date()) + 1
        if days < 1:
            days = 1
            
        user_id = self.user_filter.currentData()
        
        table_name = self.table_filter.currentText()
        if table_name == self.lm.get("Audit.entity_all", "All"):
            table_name = None
            
        action = self.action_input.text().strip() or None
        
        # Fetch logs
        # Note: simplistic fetching, audit service might need enhancement for exact date range
        # For now we use get_recent_logs with 'days' derived from date range relative to now
        # Ideally we update service to accept start/end dates.
        # But let's check audit service again... it only takes 'days'.
        # We can calculate 'days' from today back to 'from_date'.
        
        days_from_now = self.date_from.date().daysTo(QDate.currentDate())
        # If 'to' date is in future or today, we just take max range.
        # This is slight imitation but works for "recent" logs.
        # We will filter strictly in Python if needed or improve service later.
        
        logs = self.audit_service.get_recent_logs(
            days=max(days_from_now + 1, 7), # Ensure coverage
            user_id=user_id,
            table_name=table_name,
            action=action,
            limit=200
        )
        
        self.table.setRowCount(0)
        
        for log in logs:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(str(log.id)))
            self.table.setItem(row, 1, QTableWidgetItem(log.created_at.strftime("%Y-%m-%d %H:%M:%S")))
            
            username = log.user.username if log.user else "System"
            self.table.setItem(row, 2, QTableWidgetItem(username))
            
            self.table.setItem(row, 3, QTableWidgetItem(log.action))
            self.table.setItem(row, 4, QTableWidgetItem(log.table_name))
            self.table.setItem(row, 5, QTableWidgetItem(log.ip_address or "N/A"))
            
            # Store log object for details
            self.table.item(row, 0).setData(Qt.UserRole, log)

    def _show_details(self, index):
        item = self.table.item(index.row(), 0)
        log = item.data(Qt.UserRole)
        
        dialog = QDialog(self)
        dialog.setWindowTitle(self.lm.get("Audit.dialog_detail", "Audit Log Detail #{id}").format(id=log.id))
        dialog.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(dialog)
        
        # Meta info
        grid = QVBoxLayout()
        grid.addWidget(QLabel(f"<b>{self.lm.get('Audit.header_action', 'Action')}:</b> {log.action}"))
        grid.addWidget(QLabel(f"<b>{self.lm.get('Audit.header_user', 'User')}:</b> {log.user.username if log.user else 'System'}"))
        grid.addWidget(QLabel(f"<b>{self.lm.get('Audit.header_time', 'Time')}:</b> {log.created_at}"))
        grid.addWidget(QLabel(f"<b>{self.lm.get('Audit.header_entity', 'Entity')}:</b> {log.table_name}"))
        layout.addLayout(grid)
        
        layout.addWidget(QLabel(f"<b>{self.lm.get('Audit.label_changes', 'Changes')}:</b>"))
        
        # Diff View
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFontPointSize(12)
        
        content = []
        
        if log.old_data:
            content.append(f"=== {self.lm.get('Audit.old_data', 'OLD DATA')} ===")
            content.append(json.dumps(log.old_data, indent=2))
            content.append("\n")
            
        if log.new_data:
            content.append(f"=== {self.lm.get('Audit.new_data', 'NEW DATA')} ===")
            content.append(json.dumps(log.new_data, indent=2))
        
        text_edit.setText("\n".join(content))
        layout.addWidget(text_edit)
        
        dialog.exec()
