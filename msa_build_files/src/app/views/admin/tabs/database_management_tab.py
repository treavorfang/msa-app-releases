# src/app/views/admin/tabs/database_management_tab.py
import os
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, 
    QCheckBox, QLineEdit, QFileDialog, QMessageBox, QMenu, QFormLayout
)
from PySide6.QtCore import Qt, QSettings, QDir
from PySide6.QtGui import QAction, QIcon

from config.config import SETTINGS_ORGANIZATION, SETTINGS_APPLICATION, BACKUP_DIR
from services.backup_service import BackupService
from utils.language_manager import language_manager

class DatabaseManagementTab(QWidget):
    """Tab for managing database backups and restoration."""
    
    def __init__(self, container, admin_user):
        super().__init__()
        self.container = container
        self.admin_user = admin_user
        self.lm = language_manager
        
        # Initialize settings
        self.settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
        
        # Initialize Backup Service with current settings
        self._init_backup_service()
        
        self._setup_ui()
        self._load_settings()
        self.refresh_backups()
        
    def _init_backup_service(self):
        """Initialize or re-initialize backup service with configured path."""
        path = self.settings.value("database/backup_path")
        self.backup_service = BackupService(backup_dir=path)
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # --- Settings Section ---
        settings_group = QGroupBox(self.lm.get("DB.settings_group", "Backup Settings"))
        settings_layout = QFormLayout(settings_group)
        settings_layout.setSpacing(15)
        
        # 1. Backup Location
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        self.path_input.setPlaceholderText(str(BACKUP_DIR))
        path_layout.addWidget(self.path_input)
        
        browse_btn = QPushButton(self.lm.get("DB.btn_browse", "Browse..."))
        browse_btn.clicked.connect(self._browse_location)
        path_layout.addWidget(browse_btn)
        
        settings_layout.addRow(self.lm.get("DB.label_location", "Backup Location:"), path_layout)
        
        # 2. Backup on Exit
        self.backup_on_exit_cb = QCheckBox(self.lm.get("DB.cb_backup_on_exit", "Backup database automatically when application closes"))
        self.backup_on_exit_cb.toggled.connect(self._save_backup_on_exit)
        settings_layout.addRow(self.lm.get("DB.label_auto_backup", "Auto-Backup:"), self.backup_on_exit_cb)
        
        layout.addWidget(settings_group)
        
        # --- Actions Section ---
        actions_group = QGroupBox(self.lm.get("DB.actions_group", "Quick Actions"))
        actions_layout = QHBoxLayout(actions_group)
        
        backup_now_btn = QPushButton(self.lm.get("DB.btn_backup_now", "Backup Now"))
        backup_now_btn.setIcon(QIcon(":/icons/save.png"))  # Placeholder icon
        backup_now_btn.setStyleSheet("background-color: #3B82F6; color: white; font-weight: bold; padding: 8px 16px; border-radius: 4px;")
        backup_now_btn.clicked.connect(self.backup_now)
        actions_layout.addWidget(backup_now_btn)
        
        # Restore/Delete buttons (state controlled by selection)
        self.restore_btn = QPushButton(self.lm.get("DB.btn_restore", "Restore Selected"))
        self.restore_btn.setStyleSheet("background-color: #F59E0B; color: white; padding: 8px 16px; border-radius: 4px;")
        self.restore_btn.setEnabled(False)
        self.restore_btn.clicked.connect(self.restore_selected)
        actions_layout.addWidget(self.restore_btn)
        
        self.delete_btn = QPushButton(self.lm.get("DB.btn_delete", "Delete Selected"))
        self.delete_btn.setStyleSheet("background-color: #EF4444; color: white; padding: 8px 16px; border-radius: 4px;")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_selected)
        actions_layout.addWidget(self.delete_btn)
        
        actions_layout.addStretch()
        layout.addWidget(actions_group)
        
        # --- Backup List ---
        list_group = QGroupBox(self.lm.get("DB.list_group", "Available Backups"))
        list_layout = QVBoxLayout(list_group)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            self.lm.get("DB.header_filename", "Filename"),
            self.lm.get("DB.header_size", "Size"),
            self.lm.get("DB.header_date", "Created Date")
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Context Menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        list_layout.addWidget(self.table)
        
        refresh_btn = QPushButton(self.lm.get("DB.btn_refresh", "Refresh List"))
        refresh_btn.clicked.connect(self.refresh_backups)
        list_layout.addWidget(refresh_btn)
        
        layout.addWidget(list_group)
        
    def _load_settings(self):
        """Load settings from QSettings."""
        # Path
        path = self.settings.value("database/backup_path")
        if path:
            self.path_input.setText(path)
        else:
            self.path_input.setText(str(BACKUP_DIR))
            
        # Checkbox
        on_exit = self.settings.value("database/backup_on_exit", True, type=bool)
        self.backup_on_exit_cb.setChecked(on_exit)
        
    def _save_backup_on_exit(self, checked):
        self.settings.setValue("database/backup_on_exit", checked)
        
    def _browse_location(self):
        directory = QFileDialog.getExistingDirectory(self, self.lm.get("DB.dialog_select_dir", "Select Backup Directory"))
        if directory:
            self.path_input.setText(directory)
            self.settings.setValue("database/backup_path", directory)
            # Re-init service with new path
            self._init_backup_service()
            self.refresh_backups()
            
    def refresh_backups(self):
        self.table.setRowCount(0)
        try:
            backups = self.backup_service.list_backups()
            for backup in backups:
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # Filename
                item_name = QTableWidgetItem(backup['filename'])
                item_name.setData(Qt.UserRole, backup['filename'])
                self.table.setItem(row, 0, item_name)
                
                # Size
                size_mb = backup['size'] / (1024 * 1024)
                self.table.setItem(row, 1, QTableWidgetItem(f"{size_mb:.2f} MB"))
                
                # Date
                date_str = backup['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                self.table.setItem(row, 2, QTableWidgetItem(date_str))
        except Exception as e:
            QMessageBox.warning(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('DB.error_list_failed', 'Failed to list backups')}: {e}")
            
    def _on_selection_changed(self):
        has_sel = len(self.table.selectedItems()) > 0
        self.restore_btn.setEnabled(has_sel)
        self.delete_btn.setEnabled(has_sel)
        
    def _get_selected_filename(self):
        row = self.table.currentRow()
        if row >= 0:
            return self.table.item(row, 0).data(Qt.UserRole)
        return None
        
    def backup_now(self):
        try:
            path = self.backup_service.create_backup("manual")
            self.refresh_backups()
            QMessageBox.information(
                self, 
                self.lm.get("Common.success", "Success"), 
                self.lm.get("DB.msg_backup_success", "Backup created successfully:\n{path}").format(path=os.path.basename(path))
            )
        except Exception as e:
            QMessageBox.critical(self, self.lm.get("Common.error", "Error"), self.lm.get("DB.error_backup_failed", "Backup failed: {error}").format(error=e))
            
    def delete_selected(self):
        filename = self._get_selected_filename()
        if not filename: return
        
        reply = QMessageBox.question(
            self, self.lm.get("DB.confirm_delete_title", "Confirm Delete"), 
            self.lm.get("DB.confirm_delete_msg", "Are you sure you want to delete backup '{file}'?\nThis action cannot be undone.").format(file=filename),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.backup_service.delete_backup(filename)
                self.refresh_backups()
            except Exception as e:
                QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('DB.error_delete_failed', 'Delete failed')}: {e}")

    def restore_selected(self):
        filename = self._get_selected_filename()
        if not filename: return
        
        reply = QMessageBox.warning(
            self, self.lm.get("DB.confirm_restore_title", "Confirm Restore"), 
            self.lm.get("DB.confirm_restore_msg", "WARNING: You are about to restore database from '{file}'.\n\n1. Current data will be replaced.\n2. An automatic backup of the current state will be created first.\n3. The application will need to restart.\n\nAre you sure you want to proceed?").format(file=filename),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Attempt restore
                self.backup_service.restore_backup(filename)
                
                QMessageBox.information(
                    self, self.lm.get("DB.restore_success_title", "Restore Success"), 
                    self.lm.get("DB.restore_success_msg", "Database restored successfully.\nThe application must restart now.")
                )
                
                # Force restart/exit
                import sys
                from PySide6.QtWidgets import QApplication
                # In debug mode, we might just crash, but effectively we want exit
                QApplication.quit()
                sys.exit(0)
                
            except Exception as e:
                QMessageBox.critical(self, self.lm.get("DB.restore_failed_title", "Restore Failed"), f"{self.lm.get('DB.error_restore_failed', 'Failed to restore database')}: {e}")

    def _show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item: return
        
        menu = QMenu()
        restore_action = menu.addAction(self.lm.get("DB.menu_restore", "Restore Database"))
        delete_action = menu.addAction(self.lm.get("DB.menu_delete", "Delete Backup"))
        open_folder = menu.addAction(self.lm.get("DB.menu_open_folder", "Open Backup Folder"))
        
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        
        if action == restore_action:
            self.restore_selected()
        elif action == delete_action:
            self.delete_selected()
        elif action == open_folder:
            import platform
            import subprocess
            path = str(self.backup_service.backup_dir)
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
