from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QListWidget, QMessageBox, QFileDialog, QGroupBox, QListWidgetItem
)
from PySide6.QtCore import Qt, QSize
from services.backup_service import BackupService
from utils.language_manager import language_manager

class DataTab(QWidget):
    def __init__(self, container, user):
        super().__init__()
        self.container = container
        self.user = user
        self.lm = language_manager
        self.backup_service = BackupService()
        self._setup_ui()
        self._load_backups()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Left Side - Actions
        left_layout = QVBoxLayout()
        left_layout.setSpacing(20)
        left_layout.setAlignment(Qt.AlignTop)

        # Backup Section
        backup_group = QGroupBox(self.lm.get("Backup.title", "Backup Database"))
        backup_layout = QVBoxLayout(backup_group)
        
        backup_help = QLabel(self.lm.get("Backup.help", "Create a backup of your database to protect your data. Backups are saved in the project directory."))
        backup_help.setWordWrap(True)
        backup_help.setStyleSheet("color: #6B7280; font-style: italic;")
        backup_layout.addWidget(backup_help)
        
        create_btn = QPushButton(self.lm.get("Backup.create", "Create New Backup"))
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        create_btn.clicked.connect(self._create_backup)
        backup_layout.addWidget(create_btn)
        
        left_layout.addWidget(backup_group)
        
        # Restore Section (Hint)
        restore_group = QGroupBox(self.lm.get("Restore.title", "Restore Data"))
        restore_layout = QVBoxLayout(restore_group)
        
        restore_help = QLabel(self.lm.get("Restore.help", "Select a backup from the user list on the right and click Restore. Warning: This will overwrite current data!"))
        restore_help.setWordWrap(True)
        restore_help.setStyleSheet("color: #6B7280;")
        restore_layout.addWidget(restore_help)
        
        left_layout.addWidget(restore_group)
        
        left_frame = QWidget()
        left_frame.setLayout(left_layout)
        left_frame.setMaximumWidth(350)
        layout.addWidget(left_frame)

        # Right Side - Backup List
        right_layout = QVBoxLayout()
        
        list_label = QLabel(self.lm.get("Backup.list_title", "Available Backups"))
        list_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        right_layout.addWidget(list_label)
        
        self.backup_list = QListWidget()
        self.backup_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #F3F4F6;
            }
            QListWidget::item:selected {
                background-color: #E0F2FE;
                color: #0F172A;
            }
        """)
        right_layout.addWidget(self.backup_list)
        
        # List Actions
        actions_layout = QHBoxLayout()
        
        refresh_btn = QPushButton(self.lm.get("Common.refresh", "Refresh"))
        refresh_btn.clicked.connect(self._load_backups)
        actions_layout.addWidget(refresh_btn)
        
        actions_layout.addStretch()
        
        delete_btn = QPushButton(self.lm.get("Common.delete", "Delete"))
        delete_btn.setStyleSheet("color: #EF4444;")
        delete_btn.clicked.connect(self._delete_selected)
        actions_layout.addWidget(delete_btn)
        
        restore_btn = QPushButton(self.lm.get("Common.restore", "Restore Selected"))
        restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #2563EB; }
        """)
        restore_btn.clicked.connect(self._restore_selected)
        actions_layout.addWidget(restore_btn)
        
        right_layout.addLayout(actions_layout)
        
        layout.addLayout(right_layout)

    def _load_backups(self):
        self.backup_list.clear()
        backups = self.backup_service.list_backups()
        
        for backup in backups:
            item_text = f"{backup['filename']} \nSize: {backup['size']/1024:.1f} KB  |  Date: {backup['created_at'].strftime('%Y-%m-%d %H:%M:%S')}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, backup['filename'])
            self.backup_list.addItem(item)

    def _create_backup(self):
        try:
            path = self.backup_service.create_backup("manual")
            self._load_backups()
            QMessageBox.information(self, "Success", f"Backup created successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create backup: {e}")

    def _restore_selected(self):
        selected_items = self.backup_list.selectedItems()
        if not selected_items:
            return
            
        filename = selected_items[0].data(Qt.UserRole)
        confirm = QMessageBox.warning(
            self, 
            "Confirm Restore",
            f"Are you sure you want to restore from '{filename}'?\n\nCURRENT DATA WILL BE OVERWRITTEN!\n\nThe application will restart after restore.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                self.backup_service.restore_backup(filename)
                QMessageBox.information(self, "Success", "Database restored successfully. Please restart the application.")
                # We could try to restart automatically or rely on user
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to restore: {e}")

    def _delete_selected(self):
        selected_items = self.backup_list.selectedItems()
        if not selected_items:
            return
            
        filename = selected_items[0].data(Qt.UserRole)
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete backup '{filename}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            if self.backup_service.delete_backup(filename):
                self._load_backups()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete backup file.")
