# src/app/views/setting/tabs/users.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QListWidget, QListWidgetItem,
    QMessageBox, QGroupBox, QSplitter, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt
from utils.language_manager import language_manager
from utils.validation.message_handler import MessageHandler
from models.user import User

class UsersTab(QWidget):
    """
    Tab for managing system users.
    Allows adding, editing, and deleting users, and assigning them to branches/roles.
    """
    
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.user_repo = container.user_repository
        self.branch_controller = container.branch_controller
        self.role_service = container.role_service
        self.lm = language_manager
        
        self.current_user_id = None
        self._setup_ui()
        self._load_data()
        
    def _setup_ui(self):
        """Setup the UI with a list and specific details form"""
        main_layout = QHBoxLayout(self)
        
        # Splitter for List | Details
        splitter = QSplitter(Qt.Horizontal)
        
        # --- Left Side: User List ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel(self.lm.get("SettingsUsers.system_users", "System Users"))
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        left_layout.addWidget(title_label)
        
        # List
        self.user_list = QListWidget()
        self.user_list.itemClicked.connect(self._on_user_selected)
        left_layout.addWidget(self.user_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton(self.lm.get("SettingsUsers.add_new", "+ New User"))
        self.add_btn.clicked.connect(self._prepare_new_user)
        self.add_btn.setStyleSheet("background-color: #2563EB; color: white;")
        
        self.delete_btn = QPushButton(self.lm.get("Common.delete", "Delete"))
        self.delete_btn.clicked.connect(self._delete_user)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("background-color: #EF4444; color: white;")
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.delete_btn)
        left_layout.addLayout(btn_layout)
        
        splitter.addWidget(left_widget)
        
        # --- Right Side: User Details ---
        self.right_group = QGroupBox(self.lm.get("SettingsUsers.details", "User Details"))
        self.right_group.setEnabled(False)
        
        right_layout = QVBoxLayout(self.right_group)
        
        form_layout = QFormLayout()
        
        self.username_input = QLineEdit()
        self.fullname_input = QLineEdit()
        self.email_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("(Leave blank to keep current)")
        
        # Role Combo
        self.role_combo = QComboBox()
        
        # Branch Combo
        self.branch_combo = QComboBox()
        self.branch_combo.addItem("No Branch", None)
        
        # Active Checkbox
        self.active_check = QCheckBox(self.lm.get("SettingsUsers.is_active", "Is Active"))
        self.active_check.setChecked(True)
        
        form_layout.addRow(self.lm.get("SettingsUsers.username", "Username:"), self.username_input)
        form_layout.addRow(self.lm.get("SettingsUsers.full_name", "Full Name:"), self.fullname_input)
        form_layout.addRow(self.lm.get("SettingsUsers.email", "Email:"), self.email_input)
        form_layout.addRow(self.lm.get("SettingsUsers.password", "Password:"), self.password_input)
        form_layout.addRow(self.lm.get("SettingsUsers.role", "Role:"), self.role_combo)
        form_layout.addRow(self.lm.get("SettingsUsers.branch", "Branch:"), self.branch_combo)
        form_layout.addRow("", self.active_check)
        
        right_layout.addLayout(form_layout)
        
        # Save Button
        self.save_btn = QPushButton(self.lm.get("Common.save", "Save"))
        self.save_btn.clicked.connect(self._save_user)
        self.save_btn.setStyleSheet("background-color: #10B981; color: white; padding: 5px;")
        right_layout.addWidget(self.save_btn)
        
        right_layout.addStretch()
        
        splitter.addWidget(self.right_group)
        splitter.setSizes([300, 700])
        main_layout.addWidget(splitter)
        
    def _load_data(self):
        """Load users, roles, branches"""
        # Load Users
        self.user_list.clear()
        try:
            users = self.user_repo.list_all()
            for user in users:
                item = QListWidgetItem(f"{user.username} ({user.full_name})")
                item.setData(Qt.UserRole, user)
                self.user_list.addItem(item)
        except Exception as e:
            MessageHandler.show_error(self, "Error", f"Failed to load users: {str(e)}")

        # Load Roles
        self.role_combo.clear()
        try:
            roles = self.role_service.get_all_roles()
            for role in roles:
                self.role_combo.addItem(role.name, role.id)
        except Exception as e:
            print(f"Failed to load roles: {e}")
            
        # Load Branches
        self.branch_combo.clear()
        self.branch_combo.addItem("No Branch", None)
        try:
            branches = self.branch_controller.list_branches()
            for branch in branches:
                self.branch_combo.addItem(branch.name, branch.id)
        except Exception as e:
            print(f"Failed to load branches: {e}")

    def _on_user_selected(self, item):
        user = item.data(Qt.UserRole)
        self.current_user_id = user.id
        
        self.right_group.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self.right_group.setTitle(f"Edit User: {user.username}")
        
        self.username_input.setText(user.username)
        self.username_input.setReadOnly(True) # Cannot change username easily
        self.fullname_input.setText(user.full_name or "")
        self.email_input.setText(user.email or "")
        self.password_input.clear()
        self.active_check.setChecked(user.is_active)
        
        # Set Role
        index = self.role_combo.findData(user.role.id if user.role else None)
        if index >= 0:
            self.role_combo.setCurrentIndex(index)
            
        # Set Branch
        index = self.branch_combo.findData(user.branch.id if user.branch else None)
        if index >= 0:
            self.branch_combo.setCurrentIndex(index)
        else:
            self.branch_combo.setCurrentIndex(0) # None

    def _prepare_new_user(self):
        self.user_list.clearSelection()
        self.current_user_id = None
        
        self.right_group.setEnabled(True)
        self.delete_btn.setEnabled(False)
        self.right_group.setTitle("New User")
        
        self.username_input.setReadOnly(False)
        self.username_input.clear()
        self.fullname_input.clear()
        self.email_input.clear()
        self.password_input.clear()
        self.active_check.setChecked(True)
        self.role_combo.setCurrentIndex(0)
        self.branch_combo.setCurrentIndex(0)
        self.username_input.setFocus()

    def _save_user(self):
        username = self.username_input.text().strip()
        fullname = self.fullname_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        role_id = self.role_combo.currentData()
        branch_id = self.branch_combo.currentData()
        is_active = self.active_check.isChecked()
        
        if not username:
             MessageHandler.show_warning(self, self.lm.get("Admin.validation_error", "Validation Error"), self.lm.get("Admin.error_username_required", "Username is required."))
             return
             
        try:
            if self.current_user_id:
                # Update
                user = self.user_repo.get_by_id(self.current_user_id)
                if user:
                    user.full_name = fullname
                    user.email = email
                    user.is_active = is_active
                    
                    # Fix: Assign IDs directly to avoid type errors
                    user.role_id = int(role_id) if role_id is not None else None
                    user.branch_id = int(branch_id) if branch_id is not None else None
                        
                    if password:
                        user.set_password(password)
                        
                    self.user_repo.update_user(user)
                    MessageHandler.show_info(self, self.lm.get("Common.success", "Success"), self.lm.get("Admin.msg_user_updated", "User updated successfully."))
            else:
                # Create
                if not password:
                    MessageHandler.show_warning(self, self.lm.get("Admin.validation_error", "Validation Error"), self.lm.get("Admin.error_password_required", "Password is required for new users."))
                    return
                # Use auth service or repo to create? Repo has create_user
                user, success = self.user_repo.create_user(username, email, password)
                if success:
                    user.full_name = fullname
                    user.is_active = is_active
                    
                    # Fix: Assign IDs directly to avoid type errors
                    user.role_id = int(role_id) if role_id is not None else None
                    user.branch_id = int(branch_id) if branch_id is not None else None
                    
                    self.user_repo.update_user(user) # Save extra fields
                    MessageHandler.show_info(self, self.lm.get("Common.success", "Success"), self.lm.get("Admin.msg_user_created", "User created successfully."))
                else:
                    MessageHandler.show_error(self, self.lm.get("Common.error", "Error"), self.lm.get("Admin.msg_registration_failed", "Failed to create user (Username/Email might exist)."))
            
            self._load_data()
            self._prepare_new_user()
            
        except Exception as e:
            MessageHandler.show_error(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('Admin.msg_save_error', 'Failed to save user')}: {str(e)}")

    def _delete_user(self):
        if not self.current_user_id:
            return
        if MessageHandler.show_question(self, "Confirm", "Delete user?"):
            try:
                self.user_repo.delete_user(self.current_user_id)
                self._load_data()
                self._prepare_new_user()
            except Exception as e:
                MessageHandler.show_error(self, "Error", str(e))