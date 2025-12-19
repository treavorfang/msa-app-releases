# src/app/views/setting/tabs/branches.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QListWidget, QListWidgetItem,
    QMessageBox, QGroupBox, QSplitter
)
from PySide6.QtCore import Qt, Signal
from utils.language_manager import language_manager
from utils.validation.message_handler import MessageHandler

class BranchesTab(QWidget):
    """
    Tab for managing business branches (locations).
    Allows adding, editing, and deleting branches.
    """
    
    def __init__(self, container, user):
        super().__init__()
        self.container = container
        self.user = user
        self.branch_controller = container.branch_controller
        self.lm = language_manager
        
        self.current_branch_id = None
        self._setup_ui()
        self._load_branches()
        
    def _setup_ui(self):
        """Setup the UI with a list and specific details form"""
        main_layout = QHBoxLayout(self)
        
        # Splitter for List | Details
        splitter = QSplitter(Qt.Horizontal)
        
        # --- Left Side: Branch List ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel(self.lm.get("SettingsBranches.title", "Store Locations"))
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        left_layout.addWidget(title_label)
        
        # List
        self.branch_list = QListWidget()
        self.branch_list.itemClicked.connect(self._on_branch_selected)
        left_layout.addWidget(self.branch_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton(self.lm.get("SettingsBranches.add_new", "+ Add New Branch"))
        self.add_btn.clicked.connect(self._prepare_new_branch)
        self.add_btn.setStyleSheet("background-color: #2563EB; color: white;")
        
        self.delete_btn = QPushButton(self.lm.get("Common.delete", "Delete"))
        self.delete_btn.clicked.connect(self._delete_branch)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("background-color: #EF4444; color: white;")
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.delete_btn)
        left_layout.addLayout(btn_layout)
        
        splitter.addWidget(left_widget)
        
        # --- Right Side: Branch Details ---
        self.right_group = QGroupBox(self.lm.get("SettingsBranches.details", "Branch Details"))
        self.right_group.setEnabled(False)  # Disabled until selection
        
        right_layout = QVBoxLayout(self.right_group)
        
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.address_input = QLineEdit()
        self.phone_input = QLineEdit()
        
        form_layout.addRow(self.lm.get("SettingsBranches.name", "Name:"), self.name_input)
        form_layout.addRow(self.lm.get("SettingsBranches.address", "Address:"), self.address_input)
        form_layout.addRow(self.lm.get("SettingsBranches.phone", "Phone:"), self.phone_input)
        
        right_layout.addLayout(form_layout)
        
        # Save Button
        self.save_btn = QPushButton(self.lm.get("Common.save", "Save"))
        self.save_btn.clicked.connect(self._save_branch)
        self.save_btn.setStyleSheet("background-color: #10B981; color: white; padding: 5px;")
        right_layout.addWidget(self.save_btn)
        
        right_layout.addStretch()
        
        splitter.addWidget(self.right_group)
        
        # Set splitter sizes (30% list, 70% details)
        splitter.setSizes([300, 700])
        
        main_layout.addWidget(splitter)
        
    def _load_branches(self):
        """Load branches from controller"""
        self.branch_list.clear()
        try:
            branches = self.branch_controller.list_branches()
            for branch in branches:
                item = QListWidgetItem(f"{branch.name}")
                item.setData(Qt.UserRole, branch)  # Store object in item
                self.branch_list.addItem(item)
        except Exception as e:
            MessageHandler.show_error(self, "Error", f"Failed to load branches: {str(e)}")

    def _on_branch_selected(self, item):
        """Handle list selection"""
        branch = item.data(Qt.UserRole)
        self.current_branch_id = branch.id
        
        # Enable form and populate
        self.right_group.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self.right_group.setTitle(f"{self.lm.get('SettingsBranches.edit', 'Edit Branch')}")
        
        self.name_input.setText(branch.name)
        self.address_input.setText(branch.address or "")
        self.phone_input.setText(branch.phone or "")

    def _prepare_new_branch(self):
        """Clear form for new entry"""
        self.branch_list.clearSelection()
        self.current_branch_id = None
        
        self.right_group.setEnabled(True)
        self.delete_btn.setEnabled(False)
        self.right_group.setTitle(f"{self.lm.get('SettingsBranches.new', 'New Branch')}")
        
        self.name_input.clear()
        self.address_input.clear()
        self.phone_input.clear()
        self.name_input.setFocus()

    def _save_branch(self):
        """Save (Create or Update)"""
        name = self.name_input.text().strip()
        address = self.address_input.text().strip()
        phone = self.phone_input.text().strip()
        
        if not name:
            MessageHandler.show_warning(self, "Validation", "Branch Name is required.")
            return

        data = {
            "name": name,
            "address": address,
            "phone": phone
        }

        try:
            if self.current_branch_id:
                # Update
                success = self.branch_controller.update_branch(self.current_branch_id, data)
                if success:
                    MessageHandler.show_info(self, "Success", "Branch updated.")
            else:
                # Create
                success = self.branch_controller.create_branch(data)
                if success:
                    MessageHandler.show_info(self, "Success", "Branch created.")
            
            self._load_branches()
            self._prepare_new_branch()  # Reset form
            
        except Exception as e:
             MessageHandler.show_error(self, "Error", f"Failed to save branch: {str(e)}")

    def _delete_branch(self):
        """Delete selected branch"""
        if not self.current_branch_id:
            return
            
        if MessageHandler.show_question(
            self, 
            self.lm.get("Common.confirm_delete", "Confirm Delete"),
            self.lm.get("SettingsBranches.confirm_delete_msg", "Are you sure you want to delete this branch?")
        ):
            try:
                success = self.branch_controller.delete_branch(self.current_branch_id)
                if success:
                    MessageHandler.show_info(self, "Success", "Branch deleted.")
                    self._load_branches()
                    self._prepare_new_branch()
                else:
                    MessageHandler.show_error(self, "Error", "Failed to delete branch.")
            except Exception as e:
                MessageHandler.show_error(self, "Error", f"Failed to delete branch: {str(e)}")
