# src/app/views/admin/dashboard.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton,
    QMessageBox, QHeaderView, QLineEdit, QComboBox,
    QDialog, QFormLayout, QDialogButtonBox, QFrame,
    QScrollArea, QCheckBox, QGroupBox, QGridLayout,
    QStackedWidget, QButtonGroup
)
from PySide6.QtCore import Qt, Signal
from peewee import IntegrityError
from models.user import User
from models.role import Role
from models.permission import Permission
from models.role_permission import RolePermission
from models.branch import Branch
from interfaces.irole_service import IRoleService
from interfaces.iauth_service import IAuthService
from views.components.metric_card import MetricCard

from views.setting.tabs.business import BusinessSettingsTab
from views.admin.tabs.audit_log_tab import AuditLogTab
from views.admin.tabs.health_monitor_tab import HealthMonitorTab
from views.admin.tabs.database_management_tab import DatabaseManagementTab
from views.setting.tabs.customization import CustomizationTab
from utils.language_manager import language_manager
from utils.security.password_utils import hash_password, verify_password

class AdminDashboard(QWidget):
    user_updated = Signal()
    
    def __init__(self, admin_user: User, container):
        super().__init__()
        self.admin_user = admin_user
        self.container = container
        self.role_service: IRoleService = container.role_service
        self.auth_service: IAuthService = container.auth_service
        self.audit_service = container.audit_service
        self.lm = language_manager
        
        self.setWindowTitle(self.lm.get("Admin.dashboard_title", "Admin Dashboard & Control Panel"))
        
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # 1. User Management
        self.users_tab = QWidget()
        self.setup_users_tab()
        self.tabs.addTab(self.users_tab, self.lm.get("Admin.tab_user_management", "User Management"))
        
        # 2. Roles & Access
        self.roles_tab = QWidget()
        self.setup_roles_tab()
        self.tabs.addTab(self.roles_tab, self.lm.get("Admin.tab_roles_access", "Roles & Access Control"))
        
        # 3. Business Settings
        self.business_tab = BusinessSettingsTab(self.container, self.admin_user)
        self.tabs.addTab(self.business_tab, self.lm.get("Admin.tab_business_settings", "Business Settings"))
        
        # 3.1 Customization
        self.customization_tab = CustomizationTab(self.container, self.admin_user)
        self.tabs.addTab(self.customization_tab, self.lm.get("Admin.tab_customization", "Customization"))
        
        # 4. Audit Log
        self.audit_log_tab = AuditLogTab(self.container, self.admin_user)
        self.tabs.addTab(self.audit_log_tab, self.lm.get("Admin.tab_audit_log", "Audit Log"))
        
        # 5. Database Management
        self.db_tab = DatabaseManagementTab(self.container, self.admin_user)
        self.tabs.addTab(self.db_tab, self.lm.get("Admin.database_management", "Database Management"))
        
        # 6. Health Monitor
        self.health_tab = HealthMonitorTab(self.container)
        self.tabs.addTab(self.health_tab, self.lm.get("Admin.tab_system_health", "System Health"))
        
        # 7. Permission Registry (Keep or optional?)
        self.permissions_tab = QWidget()
        self.setup_permissions_tab()
        self.tabs.addTab(self.permissions_tab, self.lm.get("Admin.tab_permission_registry", "Permission Registry"))
        
        # Load initial data
        # self.load_users()
        # self.load_roles()
        # self.load_permissions()
        self._data_loaded = False
        
    def setup_users_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)
        
        # 1. Statistics Cards
        self.user_stats_layout = QHBoxLayout()
        self.user_stats_layout.setSpacing(12)
        
        # Define stats: (key, icon, label, color)
        stats_def = [
            ("total", "👥", self.lm.get("Admin.users_total", "Total Users"), "#3B82F6"), # Blue
            ("active", "✅", self.lm.get("Admin.users_active", "Active Users"), "#10B981"), # Green
            ("disabled", "🚫", self.lm.get("Admin.users_disabled", "Disabled"), "#EF4444"), # Red
            ("new", "✨", self.lm.get("Admin.users_new_today", "New Today"), "#8B5CF6") # Purple
        ]
        
        self.user_metrics = {}
        for key, icon, label, color in stats_def:
            card = MetricCard(icon, "0", label, None, color)
            card.setFixedHeight(100)
            self.user_stats_layout.addWidget(card)
            self.user_metrics[key] = card
            
        layout.addLayout(self.user_stats_layout)
        
        # 2. Controls Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.lm.get("Admin.search_placeholder", "🔍 Search users by name or email..."))
        self.search_input.setMinimumWidth(280)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border-radius: 6px;
                border: 1px solid #4B5563;
                background-color: #1F2937; 
                color: white;
            }
            QLineEdit:focus { border: 1px solid #3B82F6; }
        """)
        self.search_input.textChanged.connect(self.load_users)
        toolbar.addWidget(self.search_input)
        
        # Filter
        self.role_filter = QComboBox()
        self.role_filter.addItem(self.lm.get("Admin.role_filter_all", "All Roles"), None)
        self.role_filter.setMinimumWidth(200)
        self.role_filter.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border-radius: 6px;
                border: 1px solid #4B5563;
                background-color: #1F2937;
                color: white;
            }
        """)
        self.role_filter.currentIndexChanged.connect(self.load_users)
        toolbar.addWidget(self.role_filter)
        
        toolbar.addStretch()
        
        # View Switcher
        view_btn_style = """
            QPushButton {
                padding: 8px 16px;
                background-color: transparent;
                border: 1px solid #4B5563;
                border-radius: 6px;
                color: #D1D5DB;
            }
            QPushButton:checked {
                background-color: #3B82F6;
                border-color: #3B82F6;
                color: white;
            }
            QPushButton:hover { background-color: rgba(59, 130, 246, 0.1); }
        """
        
        self.user_view_card_btn = QPushButton(self.lm.get("Admin.view_cards", "📇 Cards"))
        self.user_view_card_btn.setCheckable(True)
        self.user_view_card_btn.setChecked(True)
        self.user_view_card_btn.setStyleSheet(view_btn_style)
        self.user_view_card_btn.clicked.connect(lambda: self._switch_user_view('cards'))
        
        self.user_view_list_btn = QPushButton(self.lm.get("Admin.view_list", "📋 List"))
        self.user_view_list_btn.setCheckable(True)
        self.user_view_list_btn.setStyleSheet(view_btn_style)
        self.user_view_list_btn.clicked.connect(lambda: self._switch_user_view('list'))
        
        group = QButtonGroup(self)
        group.addButton(self.user_view_card_btn)
        group.addButton(self.user_view_list_btn)
        
        toolbar.addWidget(self.user_view_card_btn)
        toolbar.addWidget(self.user_view_list_btn)
        
        layout.addLayout(toolbar)
        
        # 3. Actions Toolbar (Enabled on selection)
        actions_bar = QHBoxLayout()
        actions_bar.setSpacing(8)
        
        self.user_actions = []
        
        def create_action_btn(label, icon, func, primary=False):
            btn = QPushButton(f"{icon} {label}")
            if primary:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3B82F6; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold;
                    }
                    QPushButton:hover { background-color: #2563EB; }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #374151; color: white; border: none; padding: 8px 16px; border-radius: 6px;
                    }
                    QPushButton:disabled { color: #6B7280; background-color: #1F2937; }
                    QPushButton:hover:!disabled { background-color: #4B5563; }
                """)
            btn.clicked.connect(func)
            return btn
            
        btn_edit = create_action_btn(self.lm.get("Admin.action_edit", "Edit"), "✏️", self._action_edit_user)
        self.user_actions.append(btn_edit)
        
        btn_role = create_action_btn(self.lm.get("Admin.action_assign_role", "Assign Role"), "👤", self._action_assign_role)
        self.user_actions.append(btn_role)
        
        btn_status = create_action_btn(self.lm.get("Admin.action_toggle_status", "Toggle Status"), "🔄", self._action_toggle_status)
        self.user_actions.append(btn_status)
        
        for btn in self.user_actions:
            btn.setEnabled(False)
            actions_bar.addWidget(btn)
        
        actions_bar.addStretch()
        
        # Add User Button (Always right aligned in action bar or separate)
        btn_add = create_action_btn(self.lm.get("Admin.action_new_user", "New User"), "➕", self.add_user, primary=True)
        actions_bar.addWidget(btn_add)
        
        layout.addLayout(actions_bar)
        
        # 4. View Stack
        self.users_view_stack = QStackedWidget()
        
        # Card View
        self.users_card_scroll = QScrollArea()
        self.users_card_scroll.setWidgetResizable(True)
        self.users_card_scroll.setFrameShape(QFrame.NoFrame)
        self.users_card_scroll.setStyleSheet("background: transparent;") # Transparent track
        
        self.users_card_container = QWidget()
        self.users_card_container.setObjectName("cardContainer")
        # Use FlowLayout logic via GridLayout (responsive)
        self.users_card_layout = QGridLayout(self.users_card_container)
        self.users_card_layout.setSpacing(16)
        self.users_card_layout.setContentsMargins(4, 4, 4, 4)
        self.users_card_scroll.setWidget(self.users_card_container)
        self.users_view_stack.addWidget(self.users_card_scroll)
        
        # List View
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels([
            self.lm.get("Admin.header_user_info", "User Info"),
            self.lm.get("Admin.header_role", "Role"),
            self.lm.get("Admin.header_status", "Status"),
            self.lm.get("Admin.header_last_login", "Last Login")
        ])
        self.users_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setSelectionMode(QTableWidget.SingleSelection)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setStyleSheet("QTableWidget { background-color: #1F2937; border-radius: 8px; }")
        self.users_table.itemSelectionChanged.connect(self._on_user_selection_changed)
        self.users_table.doubleClicked.connect(self._action_edit_user)
        self.users_view_stack.addWidget(self.users_table)
        
        layout.addWidget(self.users_view_stack)
        self.users_tab.setLayout(layout)
        
        self.selected_user = None 
        self.current_user_view = 'cards'

    def setup_roles_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)
        
        # Stats
        self.role_stats_layout = QHBoxLayout()
        self.role_stats_layout.setSpacing(12)
        
        stats_def = [
            ("total_roles", "🛡️", self.lm.get("Admin.stats_total_roles", "Total Roles"), "#F59E0B"), # Orange
            ("total_perms", "🔑", self.lm.get("Admin.stats_system_perms", "System Permissions"), "#EC4899") # Pink
        ]
        self.role_metrics = {}
        for key, icon, label, color in stats_def:
            card = MetricCard(icon, "0", label, None, color)
            card.setFixedHeight(100)
            self.role_stats_layout.addWidget(card)
            self.role_metrics[key] = card
        
        self.role_stats_layout.addStretch() # Fill space since only 2 cards
        layout.addLayout(self.role_stats_layout)
        
        # Toolbar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)
        
        self.new_role_name = QLineEdit()
        self.new_role_name.setPlaceholderText(self.lm.get("Admin.new_role_name", "New Role Name"))
        self.new_role_name.setStyleSheet("padding: 8px; border-radius: 6px; background: #1F2937; color: white;")
        
        self.new_role_desc = QLineEdit()
        self.new_role_desc.setPlaceholderText(self.lm.get("Admin.description_placeholder", "Description"))
        self.new_role_desc.setStyleSheet("padding: 8px; border-radius: 6px; background: #1F2937; color: white;")
        
        add_btn = QPushButton(f"➕ {self.lm.get('Admin.btn_create_role', 'Create Role')}")
        add_btn.setStyleSheet("background-color: #3B82F6; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        add_btn.clicked.connect(self.add_role)
        
        top_bar.addWidget(self.new_role_name)
        top_bar.addWidget(self.new_role_desc)
        top_bar.addWidget(add_btn)
        top_bar.addStretch()
        
        # View Switcher
        view_btn_style = """
            QPushButton {
                padding: 8px 16px;
                background-color: transparent;
                border: 1px solid #4B5563;
                border-radius: 6px;
                color: #D1D5DB;
            }
            QPushButton:checked {
                background-color: #3B82F6;
                border-color: #3B82F6;
                color: white;
            }
        """
        self.role_view_card_btn = QPushButton(self.lm.get("Admin.view_cards", "📇 Cards"))
        self.role_view_card_btn.setCheckable(True)
        self.role_view_card_btn.setChecked(True)
        self.role_view_card_btn.setStyleSheet(view_btn_style)
        self.role_view_card_btn.clicked.connect(lambda: self._switch_role_view('cards'))
        
        self.role_view_list_btn = QPushButton(self.lm.get("Admin.view_list", "📋 List"))
        self.role_view_list_btn.setCheckable(True)
        self.role_view_list_btn.setStyleSheet(view_btn_style)
        self.role_view_list_btn.clicked.connect(lambda: self._switch_role_view('list'))
        
        r_group = QButtonGroup(self)
        r_group.addButton(self.role_view_card_btn)
        r_group.addButton(self.role_view_list_btn)
        
        top_bar.addWidget(self.role_view_card_btn)
        top_bar.addWidget(self.role_view_list_btn)
        
        layout.addLayout(top_bar)
        
        # Actions
        action_layout = QHBoxLayout()
        self.role_actions = []
        btn_perms = QPushButton(self.lm.get("Admin.btn_manage_permissions", "🔑 Manage Permissions"))
        btn_perms.setStyleSheet("""
             QPushButton {
                background-color: #374151; color: white; border: none; padding: 8px 16px; border-radius: 6px;
             }
             QPushButton:disabled { color: #6B7280; background-color: #1F2937; }
        """)
        btn_perms.clicked.connect(self._action_manage_perms)
        self.role_actions.append(btn_perms)
        
        for btn in self.role_actions:
            btn.setEnabled(False)
            action_layout.addWidget(btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        # View Stack
        self.roles_view_stack = QStackedWidget()
        
        self.roles_card_scroll = QScrollArea()
        self.roles_card_scroll.setWidgetResizable(True)
        self.roles_card_scroll.setFrameShape(QFrame.NoFrame)
        self.roles_card_scroll.setStyleSheet("background: transparent;")
        self.roles_card_container = QWidget()
        self.roles_card_layout = QGridLayout(self.roles_card_container)
        self.roles_card_layout.setSpacing(16)
        self.roles_card_scroll.setWidget(self.roles_card_container)
        self.roles_view_stack.addWidget(self.roles_card_scroll)
        
        self.roles_table = QTableWidget()
        self.roles_table.setColumnCount(3)
        self.roles_table.setHorizontalHeaderLabels([
            self.lm.get("Admin.header_role", "Role"),
            self.lm.get("Admin.header_description", "Description"),
            self.lm.get("Admin.header_assigned_users", "Assigned Users")
        ])
        self.roles_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.roles_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.roles_table.setSelectionMode(QTableWidget.SingleSelection)
        self.roles_table.setAlternatingRowColors(True)
        self.roles_table.setStyleSheet("QTableWidget { background-color: #1F2937; border-radius: 8px; }")
        self.roles_table.itemSelectionChanged.connect(self._on_role_selection_changed)
        self.roles_view_stack.addWidget(self.roles_table)
        
        layout.addWidget(self.roles_view_stack)
        self.roles_tab.setLayout(layout)
        
        self.selected_role = None 
        self.current_role_view = 'cards'

    def setup_permissions_tab(self):
        layout = QVBoxLayout()
        self.permissions_table = QTableWidget()
        self.permissions_table.setColumnCount(3)
        self.permissions_table.setHorizontalHeaderLabels([
            self.lm.get("Admin.header_category", "Category"),
            self.lm.get("Admin.header_perm_code", "Permission Code"),
            self.lm.get("Admin.header_description", "Description")
        ])
        self.permissions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.permissions_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.permissions_table)
        self.permissions_tab.setLayout(layout)

    def _switch_user_view(self, mode):
        self.current_user_view = mode
        if mode == 'cards':
            self.users_view_stack.setCurrentWidget(self.users_card_scroll)
        else:
            self.users_view_stack.setCurrentWidget(self.users_table)
        self.load_users()

    def _switch_role_view(self, mode):
        self.current_role_view = mode
        if mode == 'cards':
            self.roles_view_stack.setCurrentWidget(self.roles_card_scroll)
        else:
            self.roles_view_stack.setCurrentWidget(self.roles_table)
        self.load_roles()

    def _on_user_card_clicked(self, user):
        self.selected_user = user
        self._update_user_actions_state()
        # Visual feedback: Refresh cards to show selection (simplified)
        self.load_users() 

    def _on_role_card_clicked(self, role):
        self.selected_role = role
        self._update_role_actions_state()
        self.load_roles()

    def _update_user_actions_state(self):
        has_sel = self.selected_user is not None
        for btn in self.user_actions:
            btn.setEnabled(has_sel)

    def _update_role_actions_state(self):
        has_sel = self.selected_role is not None
        for btn in self.role_actions:
            btn.setEnabled(has_sel)

    def _on_user_selection_changed(self):
        # Determine selection from table if in list mode
        if self.current_user_view == 'list':
            row = self.users_table.currentRow()
            if row >= 0:
                self.selected_user = self.users_table.item(row, 0).data(Qt.UserRole)
            else:
                self.selected_user = None
        self._update_user_actions_state()
            
    def _on_role_selection_changed(self):
        if self.current_role_view == 'list':
            row = self.roles_table.currentRow()
            if row >= 0:
                self.selected_role = self.roles_table.item(row, 0).data(Qt.UserRole)
            else:
                self.selected_role = None
        self._update_role_actions_state()

    def _get_selected_user(self):
        return self.selected_user
        
    def _get_selected_role(self):
        return self.selected_role

    def _action_edit_user(self):
        user = self._get_selected_user()
        if user: self.edit_user(user)
        
    def _action_assign_role(self):
        user = self._get_selected_user()
        if user: self.show_role_assignment_dialog(user)
        
    def _action_toggle_status(self):
        user = self._get_selected_user()
        if user: self.toggle_user(user)

    def _action_manage_perms(self):
        role = self._get_selected_role()
        if role: self.manage_role_permissions(role)

    def load_users(self):
        query = User.select()
        search = self.search_input.text().lower()
        if search:
            query = query.where(User.username.contains(search) | User.email.contains(search))
        
        role_filter = self.role_filter.currentData()
        if role_filter:
            query = query.where(User.role == role_filter)
        
        users = list(query) # Materialize
        
        # Update Stats
        self.user_metrics['total'].update_value(str(len(users)))
        active_count = sum(1 for u in users if u.is_active)
        self.user_metrics['active'].update_value(str(active_count))
        self.user_metrics['disabled'].update_value(str(len(users) - active_count))
        # Logic for 'new' could be based on created_at today, using placeholder for now
        self.user_metrics['new'].update_value("0") 
        
        if self.current_user_view == 'list':
            self.users_table.setRowCount(0)
            self.users_table.blockSignals(True)
            for user in users:
                row = self.users_table.rowCount()
                self.users_table.insertRow(row)
                
                info = f"{user.username}\n{user.email}"
                item = QTableWidgetItem(info)
                item.setData(Qt.UserRole, user)
                self.users_table.setItem(row, 0, item)
                
                role_name = user.role.name if user.role else "No Role"
                self.users_table.setItem(row, 1, QTableWidgetItem(role_name))
                
                status_text = "Active" if user.is_active else "Disabled"
                status = QTableWidgetItem(status_text)
                status.setForeground(Qt.green if user.is_active else Qt.red)
                self.users_table.setItem(row, 2, status)
                self.users_table.setItem(row, 3, QTableWidgetItem("-"))
                
                if self.selected_user and self.selected_user.id == user.id:
                    self.users_table.selectRow(row)
            self.users_table.blockSignals(False)
        else:
            # Cards
            while self.users_card_layout.count():
                child = self.users_card_layout.takeAt(0)
                if child.widget(): child.widget().deleteLater()
            
            row, col = 0, 0
            cols = 4 # 4 columns like ticket view
            for user in users:
                card = self._create_user_card(user)
                self.users_card_layout.addWidget(card, row, col)
                col += 1
                if col >= cols:
                    col = 0
                    row += 1

    def _create_user_card(self, user):
        card = QFrame()
        is_selected = self.selected_user and self.selected_user.id == user.id
        
        # Premium Card Style
        bg_color = "#374151"
        border_color = "#4B5563"
        if is_selected:
            bg_color = "rgba(59, 130, 246, 0.2)"
            border_color = "#3B82F6"
        
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
            QFrame:hover {{
                border-color: #60A5FA;
            }}
        """)
        card.setFixedSize(240, 160)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header: Avatar + Status
        header = QHBoxLayout()
        avatar = QLabel(user.username[:1].upper())
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("""
            background-color: #3B82F6; color: white; border-radius: 16px; font-weight: bold; font-size: 14px; border: none;
        """)
        header.addWidget(avatar)
        
        header.addStretch()
        
        status_lbl = QLabel("ACTIVE" if user.is_active else "DISABLED")
        s_color = "#10B981" if user.is_active else "#EF4444"
        s_bg = "rgba(16, 185, 129, 0.1)" if user.is_active else "rgba(239, 68, 68, 0.1)"
        status_lbl.setStyleSheet(f"""
            color: {s_color}; background-color: {s_bg}; 
            padding: 4px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; border: none;
        """)
        header.addWidget(status_lbl)
        layout.addLayout(header)
        
        # User Info
        name = QLabel(user.username)
        name.setStyleSheet("color: white; font-weight: bold; font-size: 16px; border: none; background: transparent;")
        layout.addWidget(name)
        
        role_name = user.role.name if user.role else "No Role"
        role_lbl = QLabel(f"🛡️ {role_name}")
        role_lbl.setStyleSheet("color: #9CA3AF; font-size: 12px; border: none; background: transparent;")
        layout.addWidget(role_lbl)
        
        email_lbl = QLabel(user.email)
        email_lbl.setStyleSheet("color: #6B7280; font-size: 11px; border: none; background: transparent;")
        email_lbl.setWordWrap(True)
        layout.addWidget(email_lbl)
        
        layout.addStretch()
        
        card.mousePressEvent = lambda e: self._on_user_card_clicked(user)
        card.mouseDoubleClickEvent = lambda e: self._action_edit_user()
        return card

    def load_roles(self):
        # Refresh combo filter too
        current_data = self.role_filter.currentData()
        self.role_filter.blockSignals(True)
        self.role_filter.clear()
        self.role_filter.addItem("All Roles", None)
        
        roles = list(Role.select())
        for r in roles:
            self.role_filter.addItem(r.name, r.id)
            
        # Update Stats
        self.role_metrics['total_roles'].update_value(str(len(roles)))
        count_perms = Permission.select().count()
        self.role_metrics['total_perms'].update_value(str(count_perms))
        
        idx = self.role_filter.findData(current_data)
        if idx >= 0: self.role_filter.setCurrentIndex(idx)
        self.role_filter.blockSignals(False)
        
        if self.current_role_view == 'list':
            self.roles_table.setRowCount(0)
            self.roles_table.blockSignals(True)
            for role in roles:
                row = self.roles_table.rowCount()
                self.roles_table.insertRow(row)
                item = QTableWidgetItem(role.name)
                item.setData(Qt.UserRole, role)
                self.roles_table.setItem(row, 0, item)
                self.roles_table.setItem(row, 1, QTableWidgetItem(role.description))
                count = User.select().where(User.role == role).count()
                self.roles_table.setItem(row, 2, QTableWidgetItem(str(count)))
                
                if self.selected_role and self.selected_role.id == role.id:
                    self.roles_table.selectRow(row)
            self.roles_table.blockSignals(False)
        else:
            # Cards
            while self.roles_card_layout.count():
                child = self.roles_card_layout.takeAt(0)
                if child.widget(): child.widget().deleteLater()
                
            row, col = 0, 0
            cols = 4
            for role in roles:
                card = self._create_role_card(role)
                self.roles_card_layout.addWidget(card, row, col)
                col += 1
                if col >= cols:
                    col = 0
                    row += 1

    def _create_role_card(self, role):
        card = QFrame()
        is_selected = self.selected_role and self.selected_role.id == role.id
        
        bg = "#374151"
        border = "#4B5563"
        if is_selected:
            bg = "rgba(59, 130, 246, 0.2)"
            border = "#3B82F6"
            
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 12px;
            }}
            QFrame:hover {{ border-color: #60A5FA; }}
        """)
        card.setFixedSize(240, 140)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header = QHBoxLayout()
        icon = QLabel("🛡️")
        icon.setStyleSheet("font-size: 18px; border: none; background: transparent;")
        header.addWidget(icon)
        
        name = QLabel(role.name)
        name.setStyleSheet("color: white; font-weight: bold; font-size: 16px; border: none; background: transparent;")
        header.addWidget(name)
        header.addStretch()
        layout.addLayout(header)
        
        desc = QLabel(role.description)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #9CA3AF; font-size: 12px; border: none; background: transparent;")
        layout.addWidget(desc)
        
        layout.addStretch()
        
        count = User.select().where(User.role == role).count()
        count_lbl = QLabel(f"👥 {count} Assigned Users")
        count_lbl.setStyleSheet("color: #6B7280; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        layout.addWidget(count_lbl)
        
        card.mousePressEvent = lambda e: self._on_role_card_clicked(role)
        card.mouseDoubleClickEvent = lambda _: self._action_manage_perms()
        return card

    def load_permissions(self):
        self.permissions_table.setRowCount(0)
        perms = Permission.select().order_by(Permission.category, Permission.code)
        for p in perms:
            row = self.permissions_table.rowCount()
            self.permissions_table.insertRow(row)
            self.permissions_table.setItem(row, 0, QTableWidgetItem(p.category or "General"))
            self.permissions_table.setItem(row, 1, QTableWidgetItem(p.code))
            self.permissions_table.setItem(row, 2, QTableWidgetItem(p.description))

    def manage_role_permissions(self, role: Role):
        dialog = QDialog(self)

        dialog.setWindowTitle(self.lm.get("Admin.dialog_manage_perms", "Manage Permissions: {role}").format(role=role.name))
        dialog.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(dialog)
        
        # Get all perms and current perms
        all_perms = Permission.select().order_by(Permission.category)
        current_perms = {p.id for p in self.role_service.get_role_permissions(role)}
        
        # Group by category
        grouped = {}
        for p in all_perms:
            cat = p.category or self.lm.get("Admin.header_other", "Other")
            if cat not in grouped: grouped[cat] = []
            grouped[cat].append(p)
            
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        self.perm_checkboxes = {} # perm_id -> QCheckBox
        
        for category, perms in grouped.items():
            group = QGroupBox(category.upper())
            glayout = QGridLayout()
            row, col = 0, 0
            for i, p in enumerate(perms):
                cb = QCheckBox(f"{p.name} ({p.code})")
                cb.setToolTip(p.description)
                if p.id in current_perms:
                    cb.setChecked(True)
                self.perm_checkboxes[p.id] = cb
                
                glayout.addWidget(cb, i // 2, i % 2)
            group.setLayout(glayout)
            content_layout.addWidget(group)
            
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Save).setText(self.lm.get("Common.save", "Save"))
        btns.button(QDialogButtonBox.Cancel).setText(self.lm.get("Common.cancel", "Cancel"))
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addWidget(btns)
        
        if dialog.exec() == QDialog.Accepted:
            # Sync permissions
            for pid, cb in self.perm_checkboxes.items():
                is_checked = cb.isChecked()
                was_checked = pid in current_perms
                
                if is_checked and not was_checked:
                    # Add
                    p = Permission.get_by_id(pid)
                    self.role_service.add_permission_to_role(role, p.code, self.admin_user)
                elif not is_checked and was_checked:
                    # Remove
                    p = Permission.get_by_id(pid)
                    self.role_service.remove_permission_from_role(role, p.code, self.admin_user)
            
            QMessageBox.information(self, self.lm.get("Common.success", "Success"), self.lm.get("Admin.msg_perms_updated", "Permissions updated."))
            self.load_roles()

    def show_role_assignment_dialog(self, user):
        dialog = QDialog(self)
        dialog.setWindowTitle(self.lm.get("Admin.dialog_assign_role", "Assign Role to {user}").format(user=user.username))
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout(dialog)
        
        combo = QComboBox()
        roles = list(Role.select())
        for r in roles:
            combo.addItem(r.name, r.id)
            if user.role and user.role.id == r.id:
                combo.setCurrentIndex(combo.count() - 1)
        
        layout.addWidget(QLabel(self.lm.get("Admin.label_select_role", "Select Role:")))
        layout.addWidget(combo)
        
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText(self.lm.get("Common.ok", "OK"))
        btns.button(QDialogButtonBox.Cancel).setText(self.lm.get("Common.cancel", "Cancel"))
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addWidget(btns)
        
        if dialog.exec() == QDialog.Accepted:
            role_id = combo.currentData()
            role = Role.get_by_id(role_id)
            self.role_service.assign_role_to_user(user, role.name, self.admin_user)
            self.load_users()
            QMessageBox.information(self, self.lm.get("Common.success", "Success"), self.lm.get("Admin.msg_role_assigned", "User assigned to role {role}").format(role=role.name))

    def edit_user(self, user):
        # Allow editing profile and password
        dialog = QDialog(self)
        dialog.setWindowTitle(self.lm.get("Admin.dialog_edit_user", "Edit User: {user}").format(user=user.username))
        layout = QFormLayout(dialog)
        
        full_name_edit = QLineEdit(user.full_name or "")
        username_edit = QLineEdit(user.username)
        email_edit = QLineEdit(user.email)
        
        # Password fields
        old_password_edit = QLineEdit()
        old_password_edit.setEchoMode(QLineEdit.Password)
        old_password_edit.setPlaceholderText(self.lm.get("Admin.placeholder_old_password", "Enter current password to change"))
        
        password_edit = QLineEdit()
        password_edit.setEchoMode(QLineEdit.Password)
        password_edit.setPlaceholderText(self.lm.get("Admin.placeholder_password", "Leave blank to keep current"))
        
        confirm_edit = QLineEdit()
        confirm_edit.setEchoMode(QLineEdit.Password)
        confirm_edit.setPlaceholderText(self.lm.get("Admin.placeholder_confirm_password", "Confirm new password"))

        # Branch Selection
        branch_combo = QComboBox()
        branch_combo.addItem(self.lm.get("Admin.no_branch_global", "No Branch / Global"), None)
        branches = list(Branch.select())
        for b in branches:
            branch_combo.addItem(b.name, b.id)
            if user.branch and user.branch.id == b.id:
                branch_combo.setCurrentIndex(branch_combo.count() - 1)
        
        layout.addRow(self.lm.get("Admin.label_full_name", "Full Name:"), full_name_edit)
        layout.addRow(self.lm.get("Admin.label_username", "Username:"), username_edit)
        layout.addRow(self.lm.get("Admin.label_email", "Email:"), email_edit)
        layout.addRow(self.lm.get("Admin.label_branch", "Branch:"), branch_combo)
        layout.addRow(self.lm.get("Admin.label_old_password", "Old Password:"), old_password_edit)
        layout.addRow(self.lm.get("Admin.label_new_password", "New Password:"), password_edit)
        layout.addRow(self.lm.get("Admin.label_confirm_password_plain", "Confirm Password:"), confirm_edit)
        
        def handle_save():
            # Validate password
            old_pwd = old_password_edit.text()
            pwd = password_edit.text()
            confirm = confirm_edit.text()
            
            if pwd:
                # Verify old password
                if not verify_password(user.password_hash, old_pwd):
                    QMessageBox.warning(dialog, self.lm.get("Common.error", "Error"), self.lm.get("Admin.error_old_password_wrong", "Incorrect old password"))
                    return
                
                if pwd != confirm:
                    QMessageBox.warning(dialog, self.lm.get("Common.error", "Error"), self.lm.get("Admin.error_password_mismatch", "Passwords do not match"))
                    return
                if len(pwd) < 6:
                    QMessageBox.warning(dialog, self.lm.get("Common.error", "Error"), self.lm.get("Admin.error_password_length", "Password too short"))
                    return
                user.password_hash = hash_password(pwd)

            user.full_name = full_name_edit.text().strip()
            user.username = username_edit.text().strip()
            user.email = email_edit.text().strip()
            
            branch_id = branch_combo.currentData()
            if branch_id:
                user.branch = Branch.get_by_id(branch_id)
            else:
                user.branch = None
                
            try:
                user.save()
                self.audit_service.log_action(self.admin_user, "user_update", "users", new_data={"username": user.username, "branch_id": branch_id})
                self.load_users()
                
                msg = self.lm.get("Admin.msg_user_updated", "User updated successfully.")
                if pwd:
                    msg += "\n" + self.lm.get("Admin.msg_password_updated", "Password has been updated.")
                
                QMessageBox.information(dialog, self.lm.get("Common.success", "Success"), msg)
                dialog.accept()
            except Exception as e:
                QMessageBox.warning(dialog, self.lm.get("Common.error", "Error"), f"{self.lm.get('Admin.msg_save_error', 'Failed to save user')}: {str(e)}")

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Save).setText(self.lm.get("Common.save", "Save"))
        btns.button(QDialogButtonBox.Cancel).setText(self.lm.get("Common.cancel", "Cancel"))
        
        btns.accepted.connect(handle_save)
        btns.rejected.connect(dialog.reject)
        layout.addRow(btns)
        
        dialog.exec()

    def toggle_user(self, user):
        user.is_active = not user.is_active
        user.save()
        
        action = "enabled" if user.is_active else "disabled"
        # Localization for action text for user display
        action_text = self.lm.get("Admin.user_enabled", "enabled") if user.is_active else self.lm.get("Admin.user_disabled", "disabled")
        
        self.audit_service.log_action(self.admin_user, f"user_{action}", "users", new_data={"id": user.id})
        
        self.load_users()
        QMessageBox.information(self, self.lm.get("Common.success", "Success"), self.lm.get("Admin.msg_user_status_changed", "User {action}.").format(action=action_text))

    def add_role(self):
        name = self.new_role_name.text().strip()
        desc = self.new_role_desc.text().strip()
        if name:
            self.role_service.create_role(name, desc)
            self.new_role_name.clear()
            self.new_role_desc.clear()
            self.load_roles()

    def add_user(self):
        # Create custom dialog for better control
        dialog = QDialog(self)
        dialog.setWindowTitle(self.lm.get("Admin.dialog_create_user", "Create New User"))
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()
        
        # Inputs
        username_edit = QLineEdit()
        username_edit.setPlaceholderText(self.lm.get("Admin.placeholder_username", "Enter username"))
        
        email_edit = QLineEdit()
        email_edit.setPlaceholderText(self.lm.get("Admin.placeholder_email", "user@example.com"))
        
        password_edit = QLineEdit()
        password_edit.setEchoMode(QLineEdit.Password)
        password_edit.setPlaceholderText(self.lm.get("Admin.placeholder_password", "Password"))
        
        confirm_edit = QLineEdit()
        confirm_edit.setEchoMode(QLineEdit.Password)
        confirm_edit.setPlaceholderText(self.lm.get("Admin.placeholder_confirm_password", "Confirm Password"))
        
        # Role Selection
        role_combo = QComboBox()
        role_combo.addItem(self.lm.get("Admin.role_no_role", "No Role / Default"), None)
        roles = list(Role.select())
        for r in roles:
            role_combo.addItem(r.name, r.id)
            
        # Branch Selection
        branch_combo = QComboBox()
        branch_combo.addItem(self.lm.get("Admin.no_branch_global", "No Branch / Global"), None)
        branches = list(Branch.select())
        for b in branches:
            branch_combo.addItem(b.name, b.id)

        form_layout.addRow(self.lm.get("Admin.label_username", "Username:*"), username_edit)
        form_layout.addRow(self.lm.get("Admin.label_email", "Email:*"), email_edit)
        form_layout.addRow(self.lm.get("Admin.header_role", "Role:"), role_combo)
        form_layout.addRow(self.lm.get("Admin.label_branch", "Branch:"), branch_combo)
        form_layout.addRow(self.lm.get("Admin.label_password", "Password:*"), password_edit)
        form_layout.addRow(self.lm.get("Admin.label_confirm_password", "Confirm Password:*"), confirm_edit)
        
        layout.addLayout(form_layout)
        
        # Validation visual feedback
        error_label = QLabel()
        error_label.setStyleSheet("color: #EF4444; font-size: 12px;")
        error_label.setWordWrap(True)
        layout.addWidget(error_label)
        
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Save).setText(self.lm.get("Common.save", "Save"))
        btns.button(QDialogButtonBox.Cancel).setText(self.lm.get("Common.cancel", "Cancel"))
        
        layout.addWidget(btns)
        
        btns.rejected.connect(dialog.reject)
        
        # Custom Validation Handler
        def validate_and_save():
            u = username_edit.text().strip()
            e = email_edit.text().strip()
            p = password_edit.text().strip()
            cp = confirm_edit.text().strip()
            role_id = role_combo.currentData()
            branch_id = branch_combo.currentData()
            
            error_msg = []
            
            if not u: error_msg.append(f"- {self.lm.get('Admin.error_username_required', 'Username is required')}")
            if len(u) < 3: error_msg.append(f"- {self.lm.get('Admin.error_username_length', 'Username must be at least 3 characters')}")
            
            if not e: error_msg.append(f"- {self.lm.get('Admin.error_email_required', 'Email is required')}")
            if "@" not in e: error_msg.append(f"- {self.lm.get('Admin.error_email_invalid', 'Invalid email format')}")
            
            if not p: error_msg.append(f"- {self.lm.get('Admin.error_password_required', 'Password is required')}")
            if len(p) < 6: error_msg.append(f"- {self.lm.get('Admin.error_password_length', 'Password must be at least 6 characters')}")
            if p != cp: error_msg.append(f"- {self.lm.get('Admin.error_password_mismatch', 'Passwords do not match')}")
            
            if error_msg:
                error_label.setText("\n".join(error_msg))
                return
            
            # Attempt Registration
            try:
                success, msg = self.auth_service.register_user(u, e, p)
                if success:
                    # If role selected, assign it
                    if role_id:
                        # Need to fetch the newly created user
                        new_user = User.get_or_none(User.username == u)
                        if new_user:
                            role_obj = Role.get_by_id(role_id)
                            self.role_service.assign_role_to_user(new_user, role_obj.name, self.admin_user)
                    
                    # If branch selected, assign it
                    if branch_id:
                        # Re-fetch if needed, or use existing object
                        new_user = User.get_by_id(new_user.id) # Ensure fresh
                        new_user.branch = Branch.get_by_id(branch_id)
                        new_user.save()
                    
                    QMessageBox.information(self, self.lm.get("Common.success", "Success"), self.lm.get("Admin.msg_user_created", "User {user} created successfully.").format(user=u))
                    self.load_users()
                    dialog.accept()
                else:
                    error_label.setText(f"{self.lm.get('Admin.msg_registration_failed', 'Registration Failed')}: {msg}")
            except Exception as ex:
                error_label.setText(f"{self.lm.get('Admin.msg_system_error', 'System Error')}: {str(ex)}")
        
        # Connect Save button
        save_btn = btns.button(QDialogButtonBox.Save)
        save_btn.clicked.connect(validate_and_save)
        
        dialog.exec()

    def showEvent(self, event):
        """Lazy load data when tab is shown"""
        super().showEvent(event)
        if not self._data_loaded:
            # key: Use a timer to allow UI to render first
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, lambda: [
                self.load_users(),
                self.load_roles(),
                self.load_permissions()
            ])
            self._data_loaded = True