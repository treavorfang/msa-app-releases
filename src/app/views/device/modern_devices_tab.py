# src/app/views/device/modern_devices_tab.py
"""
Modern Devices Tab with enhanced UI features:
- Card/Grid view
- Advanced filtering
- Quick actions
- Bulk operations
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QCheckBox, QFrame, QScrollArea,
    QGridLayout, QStackedWidget, QDialog, QFormLayout,
    QDialogButtonBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMenu, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QCursor, QAction
from typing import List, Dict
from dtos.device_dto import DeviceDTO
from utils.validation.message_handler import MessageHandler
from views.device.device_details_dialog import DeviceDetailsDialog
from utils.language_manager import LanguageManager
from core.event_bus import EventBus
from core.events import (
    DeviceCreatedEvent, DeviceUpdatedEvent, DeviceDeletedEvent, DeviceRestoredEvent,
    TicketCreatedEvent, TicketUpdatedEvent, TicketStatusChangedEvent
)
from views.components.loading_overlay import LoadingOverlay
from views.components.new_dashboard_widgets import is_dark_theme


class ModernDevicesTab(QWidget):
    """Modern device management interface with multiple view modes"""
    
    device_selected = Signal(DeviceDTO)
    
    # Status colors
    STATUS_COLORS = {
        'received': '#4169E1',       # Royal Blue
        'diagnosed': '#20B2AA',      # Light Sea Green
        'repairing': '#FFD700',      # Gold
        'repaired': '#BA55D3',       # Medium Orchid
        'completed': '#32CD32',      # Lime Green
        'returned': '#90EE90'        # Light Green
    }
    
    def __init__(self, container, user):
        super().__init__()
        self.container = container
        self.user = user
        self.device_controller = container.device_controller
        self.customer_controller = container.customer_controller
        self.customers = []
        self.selected_devices = []
        self.current_view = 'cards'
        self.lm = LanguageManager()
        self.loading_overlay = LoadingOverlay(self)
        self._setup_ui()
        self._connect_signals()
        self._subscribe_to_events()
        self._connect_signals()
        self._subscribe_to_events()
        # self._load_customers()
        # self._load_devices()
        self._data_loaded = False
        
    def _setup_ui(self):
        """Setup the main UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Header with title and view switcher
        header_layout = self._create_header()
        layout.addLayout(header_layout)
        
        # Filters and search
        filter_layout = self._create_advanced_filters()
        layout.addLayout(filter_layout)
        

        
        # Stacked widget for different views
        self.view_stack = QStackedWidget()
        
        # Create different view widgets
        self.cards_view = self._create_cards_view()
        self.list_view = self._create_list_view()
        
        self.view_stack.addWidget(self.cards_view)
        self.view_stack.addWidget(self.list_view)
        
        layout.addWidget(self.view_stack, 1)
        
    def _create_header(self):
        """Create header with title and view switcher"""
        layout = QHBoxLayout()
        
        # Title
        title = QLabel(self.lm.get("MainWindow.devices", "Devices"))
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # View mode buttons
        view_label = QLabel(self.lm.get("Common.view", "View") + ":")
        view_label.setObjectName("metricLabel")
        layout.addWidget(view_label)
        
        self.cards_view_btn = QPushButton(self.lm.get('Invoices.view_cards', '📇 Cards'))
        self.list_view_btn = QPushButton(self.lm.get('Invoices.view_list', '📋 List'))
        
        self.cards_view_btn.setCheckable(True)
        self.list_view_btn.setCheckable(True)
        self.cards_view_btn.setChecked(True)
        
        # Style for view buttons
        view_btn_style = """
            QPushButton {
                padding: 8px 16px;
                border-radius: 6px;
                border: 1px solid #374151;
                background-color: transparent;
            }
            QPushButton:checked {
                background-color: #3B82F6;
                color: white;
                border-color: #3B82F6;
            }
            QPushButton:hover {
                background-color: rgba(59, 130, 246, 0.1);
            }
        """
        
        for btn in [self.cards_view_btn, self.list_view_btn]:
            btn.setStyleSheet(view_btn_style)
            layout.addWidget(btn)
        
        return layout
    
    def _create_advanced_filters(self):
        """Create advanced filter controls"""
        layout = QVBoxLayout()
        
        # First row - Search and filters
        row1 = QHBoxLayout()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(f"🔍 {self.lm.get('Devices.search_placeholder', 'Search by barcode, brand, model, IMEI, serial...')}")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumWidth(250)
        row1.addWidget(self.search_input)
        
        # Status filter
        self.status_filter = QComboBox()
        self.status_filter.addItem(self.lm.get("Devices.all_statuses", "All Statuses"), "all")
        self.status_filter.addItem(self.lm.get("Common.received", "Received"), "received")
        self.status_filter.addItem(self.lm.get("Common.diagnosed", "Diagnosed"), "diagnosed")
        self.status_filter.addItem(self.lm.get("Common.repairing", "Repairing"), "repairing")
        self.status_filter.addItem(self.lm.get("Common.repaired", "Repaired"), "repaired")
        self.status_filter.addItem(self.lm.get("Common.completed", "Completed"), "completed")
        self.status_filter.addItem(self.lm.get("Common.returned", "Returned"), "returned")
        self.status_filter.setMinimumWidth(130)
        row1.addWidget(self.status_filter)
        
        # Customer filter
        self.customer_filter = QComboBox()
        self.customer_filter.setMinimumWidth(130)
        self.customer_filter.addItem(self.lm.get("Customers.all_customers", "All Customers"), "all")
        self.customer_filter.setPlaceholderText(self.lm.get("Devices.filter_by_customer", "Filter by Customer"))
        row1.addWidget(self.customer_filter)
        
        # Refresh button
        refresh_btn = QPushButton(f"🔄 {self.lm.get('Common.refresh', 'Refresh')}")
        refresh_btn.clicked.connect(self._load_devices)
        row1.addWidget(refresh_btn)
        
        # Export button with menu
        export_btn = QPushButton(f"📥 {self.lm.get('Common.export', 'Export')}")
        export_menu = QMenu(self)
        
        # CSV Action
        export_csv_action = QAction(self.lm.get("Common.export_csv", "Export CSV"), self)
        export_csv_action.triggered.connect(self._export_to_csv)
        export_menu.addAction(export_csv_action)
        
        # PDF Action
        export_pdf_action = QAction(self.lm.get("Common.export_pdf", "Export PDF"), self)
        export_pdf_action.triggered.connect(self._export_to_pdf)
        export_menu.addAction(export_pdf_action)
        
        export_btn.setMenu(export_menu)
        row1.addWidget(export_btn)
        
        layout.addLayout(row1)
        
        # Second row - Checkboxes and Actions
        row2 = QHBoxLayout()
        
        # Show deleted
        self.show_deleted_checkbox = QCheckBox(self.lm.get("Common.show_deleted", "Show Deleted"))
        row2.addWidget(self.show_deleted_checkbox)
        
        # Show returned (hide by default)
        self.show_returned_checkbox = QCheckBox(self.lm.get("Devices.show_returned", "Show Returned"))
        self.show_returned_checkbox.setToolTip(self.lm.get("Devices.show_returned_tooltip", "Show devices that have been returned to customers"))
        row2.addWidget(self.show_returned_checkbox)
        
        # Clear filters button
        clear_btn = QPushButton(f"🔄 {self.lm.get('Common.clear_filters', 'Clear Filters')}")
        clear_btn.clicked.connect(self._clear_filters)
        row2.addWidget(clear_btn)
        
        row2.addStretch()
        
        # Bulk actions
        self.bulk_update_btn = QPushButton(f"📝 {self.lm.get('Common.bulk_update', 'Bulk Update')}")
        self.bulk_update_btn.setEnabled(False)
        row2.addWidget(self.bulk_update_btn)
        
        self.bulk_delete_btn = QPushButton(f"🗑️ {self.lm.get('Customers.bulk_delete', 'Bulk Delete')}")
        self.bulk_delete_btn.setEnabled(False)
        row2.addWidget(self.bulk_delete_btn)
        
        # Barcode buttons
        self.preview_barcodes_btn = QPushButton(f"👁️ {self.lm.get('Devices.preview_barcodes', 'Preview Barcodes')}")
        self.preview_barcodes_btn.setEnabled(False)
        row2.addWidget(self.preview_barcodes_btn)
        
        self.print_barcodes_btn = QPushButton(f"🖨️ {self.lm.get('Devices.print_barcodes', 'Print Barcodes')}")
        self.print_barcodes_btn.setEnabled(False)
        row2.addWidget(self.print_barcodes_btn)
        
        # New device button (primary)
        self.new_device_btn = QPushButton(f"➕ {self.lm.get('Devices.new_device', 'New Device')}")
        self.new_device_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                padding: 6px 12px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        row2.addWidget(self.new_device_btn)
        
        layout.addLayout(row2)
        
        return layout
    
    def _update_bulk_buttons_state(self, *args):
        """Enable bulk action buttons when any row is checked or card selected"""
        any_checked = False
        
        if self.current_view == 'list':
            for row in range(self.devices_table.rowCount()):
                item = self.devices_table.item(row, 0)
                if item and item.checkState() == Qt.Checked:
                    any_checked = True
                    break
        else:
            any_checked = len(self.selected_devices) > 0
        
        self.bulk_update_btn.setEnabled(any_checked)
        self.bulk_delete_btn.setEnabled(any_checked)
        self.preview_barcodes_btn.setEnabled(any_checked)
        self.print_barcodes_btn.setEnabled(any_checked)
    

    
    def _create_cards_view(self):
        """Create card/grid view"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        # Handle background click to deselect
        container.mousePressEvent = self._on_background_clicked
        
        self.cards_layout = QGridLayout(container)
        self.cards_layout.setSpacing(12)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(container)
        return scroll
    
    def _create_list_view(self):
        """Create traditional list/table view"""
        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(9)
        headers = [
            "✓", 
            self.lm.get("Inventory.barcode", "Barcode"), 
            self.lm.get("Tickets.device_brand", "Brand"), 
            self.lm.get("Tickets.device_model", "Model"), 
            self.lm.get("Tickets.device_color", "Color"), 
            self.lm.get("Tickets.device_imei", "IMEI"), 
            self.lm.get("Tickets.device_serial", "Serial"), 
            self.lm.get("Tickets.status", "Status"), 
            self.lm.get("Tickets.customer", "Customer")
        ]
        self.devices_table.setHorizontalHeaderLabels(headers)
        
        # Set resize modes
        header = self.devices_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.sectionClicked.connect(self._on_header_clicked)
        
        self.devices_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.devices_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.devices_table.setAlternatingRowColors(True)
        self.devices_table.setColumnWidth(0, 40)
        
        return self.devices_table
    
    def _connect_signals(self):
        """Connect all signals"""
        # View switcher
        self.cards_view_btn.clicked.connect(lambda: self._switch_view('cards'))
        self.list_view_btn.clicked.connect(lambda: self._switch_view('list'))
        
        # Filters
        self.search_input.textChanged.connect(self._on_filter_changed)
        self.status_filter.currentTextChanged.connect(self._on_filter_changed)
        self.customer_filter.currentTextChanged.connect(self._on_filter_changed)
        self.show_deleted_checkbox.stateChanged.connect(self._on_filter_changed)
        self.show_returned_checkbox.stateChanged.connect(self._on_filter_changed)
        
        # Actions
        self.new_device_btn.clicked.connect(self._create_new_device)
        self.bulk_update_btn.clicked.connect(self._bulk_update_status)
        self.bulk_delete_btn.clicked.connect(self._bulk_delete_devices)
        self.preview_barcodes_btn.clicked.connect(self._preview_barcodes)
        self.print_barcodes_btn.clicked.connect(self._print_barcodes)
        self.devices_table.itemChanged.connect(self._update_bulk_buttons_state)
        
        self._connect_theme_signal()

    def _connect_theme_signal(self):
        """Connect to theme change signal"""
        if self.container and hasattr(self.container, 'theme_controller') and self.container.theme_controller:
            if hasattr(self.container.theme_controller, 'theme_changed'):
                self.container.theme_controller.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name):
        """Handle theme change"""
        self._load_devices()
        
        # Table double click
        self.devices_table.doubleClicked.connect(self._on_table_double_click)
        
        # Controller signals
        # Note: Domain events are now handled by EventBus in _subscribe_to_events
        pass
    
    def _switch_view(self, view_mode):
        """Switch between different view modes"""
        self.current_view = view_mode
        
        # Update button states
        self.cards_view_btn.setChecked(view_mode == 'cards')
        self.list_view_btn.setChecked(view_mode == 'list')
        
        # Switch view
        if view_mode == 'cards':
            self.view_stack.setCurrentWidget(self.cards_view)
        elif view_mode == 'list':
            self.view_stack.setCurrentWidget(self.list_view)
        
        # Reload devices for the new view
        self._load_devices()
    
    def _clear_filters(self):
        """Clear all filters"""
        self.search_input.clear()
        self.status_filter.setCurrentIndex(0)
        self.customer_filter.setCurrentIndex(0)
        self.show_deleted_checkbox.setChecked(False)
        self.show_returned_checkbox.setChecked(False)
    
    def _load_customers(self, *args):
        """Load customers for filter"""
        try:
            self.customers = self.customer_controller.get_all_customers()
            self._populate_customer_filter()
        except Exception as e:
            print(f"Error loading customers: {e}")
            self.customers = []
    
    def _populate_customer_filter(self):
        """Populate customer filter"""
        self.customer_filter.clear()
        self.customer_filter.addItem(self.lm.get("Customers.all_customers", "All Customers"))
        
        for customer in self.customers:
            customer_name = customer.name if customer.name else f"{self.lm.get('Customers.customer', 'Customer')} #{customer.id}"
            self.customer_filter.addItem(customer_name, customer.id)
    
    def _on_filter_changed(self, *args):
        """Handle filter changes"""
        QTimer.singleShot(300, self._load_devices)
    
    def _get_selected_device_ids(self):
        """Collect device IDs from checked rows OR selected cards"""
        if self.current_view == 'list':
            ids = []
            for row in range(self.devices_table.rowCount()):
                checkbox_item = self.devices_table.item(row, 0)
                if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                    device_item = self.devices_table.item(row, 1)
                    if device_item:
                        did = device_item.data(Qt.UserRole)
                        if did:
                            ids.append(did)
            return ids
        else:
            return self.selected_devices.copy()
    
    def _get_localized_status(self, status: str) -> str:
        """Get localized status text"""
        status_key_map = {
            'received': 'Common.received',
            'diagnosed': 'Common.diagnosed',
            'repairing': 'Common.repairing',
            'repaired': 'Common.repaired',
            'completed': 'Common.completed',
            'returned': 'Common.returned'
        }
        key = status_key_map.get(status.lower(), 'Common.unknown')
        return self.lm.get(key, status.capitalize())
    
    def _load_devices(self):
        """Load devices based on filters"""
        try:
            self.loading_overlay.start(self.lm.get("Common.loading_devices", "Loading devices..."))
            
            # Get filter values
            search_text = self.search_input.text().strip()
            
            # Build filters for list_devices
            filters = {}
            if self.show_deleted_checkbox.isChecked():
                filters['include_deleted'] = True
            
            customer_id = self.customer_filter.currentData()
            if customer_id and customer_id != 'all':
                filters['customer_id'] = customer_id
            
            status = self.status_filter.currentData()
            if status and status != 'all':
                filters['status'] = status

            # Fetch devices
            if search_text:
                # Search takes precedence for retrieval
                devices = self.device_controller.search_devices(search_text)
                
                # Apply remaining filters manually to search results
                if filters.get('status'):
                     devices = [d for d in devices if d.status == filters['status']]
                if filters.get('customer_id'):
                     devices = [d for d in devices if d.customer_id == filters['customer_id']]
                # Deleted are implicitly excluded usually unless restored? 
                # Assuming search returns active. If 'include_deleted', we might miss them if search ignores them.
                # But this is a safe fallback.
            else:
                devices = self.device_controller.list_devices(filters)
            
            # Sort by ID descending
            devices.sort(key=lambda x: x.id, reverse=True)

            self._current_device_list = devices
            
            # Stats update removed
            

            if self.current_view == 'cards':
                self._populate_cards_view(devices)
            elif self.current_view == 'list':
                self._populate_list_view(devices)
        except Exception as e:
            print(f"Error loading devices: {e}")
            import traceback
            traceback.print_exc()
            MessageHandler.show_error(
                self, 
                self.lm.get("Common.error", "Error"), 
                f"Failed to load devices: {str(e)}"
            )
        finally:
            if hasattr(self, 'loading_overlay'):
                self.loading_overlay.stop()
    
    def _build_filters(self) -> Dict:
        """Build filter dictionary from UI"""
        filters = {}
        
        # Include deleted
        filters['include_deleted'] = self.show_deleted_checkbox.isChecked()
        
        # Status filter
        # Status filter
        status_key = self.status_filter.currentData()
        if status_key and status_key != "all":
            filters['status'] = status_key
        
        # Customer filter
        # Customer filter
        customer_id = self.customer_filter.currentData()
        if customer_id and customer_id != "all":
            customer_id = self.customer_filter.currentData()
            if customer_id:
                filters['customer_id'] = customer_id
        
        return filters
    
    def _populate_cards_view(self, devices: List[DeviceDTO]):
        """Populate cards view"""
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add device cards
        for idx, device in enumerate(devices):
            row = idx // 3
            col = idx % 3
            card = self._create_device_card(device)
            self.cards_layout.addWidget(card, row, col)
        
        # Add stretch at the end
        self.cards_layout.setRowStretch(self.cards_layout.rowCount(), 1)
    
    def _create_device_card(self, device: DeviceDTO):
        """Create a device card widget"""
        # Theme colors
        dark_mode = is_dark_theme(self)
        
        bg_color = "#1F2937" if dark_mode else "#FFFFFF"
        border_color = "#374151" if dark_mode else "#E5E7EB"
        text_main = "white" if dark_mode else "#1F2937"
        text_sub = "#9CA3AF" if dark_mode else "#6B7280"
        
        card = QFrame()
        card.setObjectName("deviceCard")
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.setMinimumHeight(180)
        card.setMaximumHeight(220)
        
        # Initial style is handled by _update_card_selection_style logic or here for base
        # We set base logic in _update_card_selection_style but consistent fallback here
        card.setStyleSheet(f"""
            QFrame#deviceCard {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
            QFrame#deviceCard:hover {{
                border-color: #3B82F6;
                background-color: {bg_color};
            }}
        """)
        
        # Store device data
        card.device_id = device.id
        card.device_dto = device
        
        # Custom event handling
        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                self._on_card_clicked(card, device)
                event.accept()
            else:
                QFrame.mousePressEvent(card, event)
            
        def mouseDoubleClickEvent(event):
            if event.button() == Qt.LeftButton:
                self._on_card_double_clicked(device)
                
        card.mousePressEvent = mousePressEvent
        card.mouseDoubleClickEvent = mouseDoubleClickEvent
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Header row - Barcode and status
        header = QHBoxLayout()
        
        barcode = QLabel(device.barcode or self.lm.get("Devices.no_barcode", "No Barcode"))
        barcode.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {text_main};")
        header.addWidget(barcode)
        
        header.addStretch()
        
        # Status badge
        status_text = self._get_localized_status(device.status)
        status_badge = QLabel(status_text.upper())
        status_color = self.STATUS_COLORS.get(device.status, '#6B7280')
        status_badge.setStyleSheet(f"""
            background-color: {status_color};
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: bold;
        """)
        header.addWidget(status_badge)
        
        layout.addLayout(header)
        
        # Device information
        device_info = f"{device.brand} {device.model}" if device.brand and device.model else self.lm.get("Common.unknown_device", "Unknown Device")
        device_label = QLabel(device_info)
        device_label.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {text_main};")
        layout.addWidget(device_label)
        
        # Customer
        customer = QLabel(device.customer_name if device.customer_name else self.lm.get("Common.no_customer", "No Customer"))
        customer.setStyleSheet(f"font-size: 12px; color: {text_sub};")
        layout.addWidget(customer)
        
        # Color and condition
        details = f"{self.lm.get('Devices.color', 'Color')}: {device.color or self.lm.get('Common.not_applicable', 'N/A')} | {self.lm.get('Devices.condition', 'Condition')}: {device.condition or self.lm.get('Common.not_applicable', 'N/A')}"
        details_label = QLabel(details)
        details_label.setStyleSheet(f"font-size: 11px; color: {text_sub};")
        layout.addWidget(details_label)
        
        # Lock/Passcode information
        if device.passcode:
            lock_info = f"🔒 {self.lm.get('Devices.passcode', 'Passcode')}: {device.passcode}"
            lock_label = QLabel(lock_info)
            lock_label.setStyleSheet("font-size: 10px; color: #F59E0B; font-weight: bold;")
            layout.addWidget(lock_label)
        
        layout.addStretch()
        
        # Initial style
        self._update_card_selection_style(card, device.id in self.selected_devices)
        
        return card
    
    def _populate_list_view(self, devices: List[DeviceDTO]):
        """Populate list/table view"""
        self.devices_table.setRowCount(len(devices))
        
        for row, device in enumerate(devices):
            # Checkbox
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.Unchecked)
            self.devices_table.setItem(row, 0, checkbox_item)
            
            # Barcode (store device id in UserRole)
            barcode_item = QTableWidgetItem(device.barcode or "")
            barcode_item.setData(Qt.UserRole, device.id)
            self.devices_table.setItem(row, 1, barcode_item)
            
            # Brand
            self.devices_table.setItem(row, 2, QTableWidgetItem(device.brand or ""))
            
            # Model
            self.devices_table.setItem(row, 3, QTableWidgetItem(device.model or ""))
            
            # Color
            self.devices_table.setItem(row, 4, QTableWidgetItem(device.color or ""))
            
            # IMEI
            self.devices_table.setItem(row, 5, QTableWidgetItem(device.imei or ""))
            
            # Serial
            self.devices_table.setItem(row, 6, QTableWidgetItem(device.serial_number or ""))
            
            # Status with color
            status_text = self._get_localized_status(device.status)
            status_item = QTableWidgetItem(status_text.upper())
            status_item.setForeground(QColor(self.STATUS_COLORS.get(device.status, '#6B7280')))
            self.devices_table.setItem(row, 7, status_item)
            
            # Customer
            self.devices_table.setItem(row, 8, QTableWidgetItem(device.customer_name or ""))
    
    def _on_table_double_click(self, index):
        """Open device detail dialog on double click"""
        row = index.row()
        device_item = self.devices_table.item(row, 1)
        if not device_item:
            return
        device_id = device_item.data(Qt.UserRole)
        if not device_id:
            return
        device_dto = self.device_controller.get_device(device_id)
        if device_dto:
            dialog = DeviceDetailsDialog(device_dto, parent=self)
            dialog.exec()
    
    def _on_card_clicked(self, card, device: DeviceDTO):
        """Handle card click (toggle selection)"""
        if device.id in self.selected_devices:
            self.selected_devices.remove(device.id)
            self._update_card_selection_style(card, False)
        else:
            self.selected_devices.append(device.id)
            self._update_card_selection_style(card, True)
        
        self._update_bulk_buttons_state()
        
    def _on_card_double_clicked(self, device: DeviceDTO):
        """Handle card double click (open details)"""
        dialog = DeviceDetailsDialog(device, parent=self)
        dialog.exec()
        
    def _update_card_selection_style(self, card, is_selected):
        """Update card style based on selection"""
        # Theme colors
        dark_mode = is_dark_theme(self)
        
        # Base colors
        bg_color = "#1F2937" if dark_mode else "#FFFFFF"
        border_color = "#374151" if dark_mode else "#E5E7EB"
        
        # Selection colors
        sel_bg = "#374151" if dark_mode else "#EFF6FF"
        sel_border = "#3B82F6" # Stay blue
        
        if is_selected:
            card.setStyleSheet(f"""
                QFrame#deviceCard {{
                    background-color: {sel_bg};
                    border: 2px solid {sel_border};
                    border-radius: 8px;
                }}
            """)
        else:
            card.setStyleSheet(f"""
                QFrame#deviceCard {{
                    background-color: {bg_color};
                    border: 1px solid {border_color};
                    border-radius: 8px;
                }}
                QFrame#deviceCard:hover {{
                    border-color: {sel_border};
                    background-color: {bg_color};
                }}
            """)

    def _on_background_clicked(self, event):
        """Handle click on background to deselect all"""
        if event.button() == Qt.LeftButton:
            self._deselect_all()
            
    def _deselect_all(self):
        """Deselect all cards"""
        self.selected_devices.clear()
        
        # Update style for all cards
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item and item.widget():
                self._update_card_selection_style(item.widget(), False)
        
        self._update_bulk_buttons_state()
    
    def _create_new_device(self):
        """Create new device"""
        from views.device.device_form import DeviceForm
        form = DeviceForm(None, self)
        if form.exec() == QDialog.Accepted:
            self._load_devices()
    
    def _bulk_update_status(self):
        """Bulk update status for selected devices"""
        selected_ids = self._get_selected_device_ids()
        if not selected_ids:
            MessageHandler.show_warning(self, self.lm.get("Devices.no_selection", "No devices selected"), self.lm.get("Devices.select_to_update", "Please select devices to update."))
            return
        
        # Status selection dialog - store English values as data
        status_dialog = QDialog(self)
        status_dialog.setWindowTitle(self.lm.get("Devices.bulk_update_status", "Bulk Update Status"))
        layout = QVBoxLayout(status_dialog)
        combo = QComboBox()
        
        # Define status options with localized labels
        status_options = [
            ('received', self.lm.get("Common.received", "Received")),
            ('diagnosed', self.lm.get("Common.diagnosed", "Diagnosed")),
            ('repairing', self.lm.get("Common.repairing", "Repairing")),
            ('repaired', self.lm.get("Common.repaired", "Repaired")),
            ('completed', self.lm.get("Common.completed", "Completed")),
            ('returned', self.lm.get("Common.returned", "Returned"))
        ]
        
        for status_key, status_label in status_options:
            combo.addItem(status_label, status_key)
        
        layout.addWidget(QLabel(self.lm.get("Common.select_status", "Select new status:")))
        layout.addWidget(combo)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(btns)
        btns.accepted.connect(status_dialog.accept)
        btns.rejected.connect(status_dialog.reject)
        
        if status_dialog.exec() == QDialog.Accepted:
            # Get English status value from combo box data (not the display text)
            new_status = combo.currentData()
            for did in selected_ids:
                self.device_controller.update_device(
                    did, 
                    {'status': new_status},
                    current_user=self.user.id,
                    ip_address='127.0.0.1'
                )
            MessageHandler.show_info(self, self.lm.get("Common.bulk_update", "Bulk Update"), f"{self.lm.get('Common.updated', 'Updated')} {len(selected_ids)} {self.lm.get('MainWindow.devices', 'devices')} {self.lm.get('Common.to', 'to')} {new_status}.")
            self._load_devices()
    
    def _bulk_delete_devices(self):
        """Bulk delete selected devices"""
        selected_ids = self._get_selected_device_ids()
        if not selected_ids:
            MessageHandler.show_warning(self, self.lm.get("Devices.no_selection", "No devices selected"), self.lm.get("Devices.select_to_delete", "Please select devices to delete."))
            return
        
        if MessageHandler.show_question(
            self,
            self.lm.get("Common.confirm_bulk_delete", "Confirm Bulk Delete"),
            f"{self.lm.get('Common.confirm_delete_question', 'Are you sure you want to delete')} {len(selected_ids)} {self.lm.get('MainWindow.devices', 'devices')}?"
        ):
            for did in selected_ids:
                self.device_controller.delete_device(did, self.user.id)
            MessageHandler.show_info(self, self.lm.get("Customers.bulk_delete", "Bulk Delete"), f"{self.lm.get('Common.deleted', 'Deleted')} {len(selected_ids)} {self.lm.get('MainWindow.devices', 'devices')}.")
            self._load_devices()
    
    def _on_header_clicked(self, column):
        """Handle header click for select all checkbox"""
        if column == 0:  # Checkbox column
            # Check if any are unchecked
            any_unchecked = False
            for row in range(self.devices_table.rowCount()):
                item = self.devices_table.item(row, 0)
                if item and item.checkState() == Qt.Unchecked:
                    any_unchecked = True
                    break
            
            # If any unchecked, check all. Otherwise, uncheck all
            new_state = Qt.Checked if any_unchecked else Qt.Unchecked
            
            # Block signals to avoid triggering update for each item
            self.devices_table.blockSignals(True)
            for row in range(self.devices_table.rowCount()):
                item = self.devices_table.item(row, 0)
                if item:
                    item.setCheckState(new_state)
            self.devices_table.blockSignals(False)
            
            # Update button states once
            self._update_bulk_buttons_state()
    
    def _preview_barcodes(self):
        """Preview barcodes for selected devices"""
        selected_ids = self._get_selected_device_ids()
        if not selected_ids:
            MessageHandler.show_warning(
                self, 
                self.lm.get("Devices.no_selection", "No devices selected"), 
                self.lm.get("Devices.select_to_preview", "Please select devices to preview barcodes.")
            )
            return
        
        try:
            from utils.print.barcode_generator import BarcodeGenerator
            
            # Get device details with ticket numbers
            devices = []
            for device_id in selected_ids:
                device = self.device_controller.get_device(device_id)
                if device:
                    # Get the latest ticket for this device
                    try:
                        from models.ticket import Ticket
                        latest_ticket = Ticket.select().where(
                            (Ticket.device == device_id) & 
                            (Ticket.is_deleted == False)
                        ).order_by(Ticket.created_at.desc()).first()
                        
                        if latest_ticket:
                            # Add ticket number as attribute to device DTO
                            device.ticket_number = latest_ticket.ticket_number
                    except Exception as e:
                        print(f"Error fetching ticket for device {device_id}: {e}")
                    
                    devices.append(device)
            
            if not devices:
                MessageHandler.show_warning(
                    self,
                    self.lm.get("Common.error", "Error"),
                    "No valid devices found."
                )
                return
            
            # Preview
            generator = BarcodeGenerator(self)
            if not generator.preview_barcodes(devices):
                MessageHandler.show_error(
                    self,
                    self.lm.get("Common.error", "Error"),
                    "Failed to preview barcodes"
                )
            
        except ImportError:
            MessageHandler.show_error(
                self,
                self.lm.get("Common.error", "Error"),
                "Required libraries missing. Install with: pip install weasyprint python-barcode"
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            MessageHandler.show_error(
                self,
                self.lm.get("Common.error", "Error"),
                f"Failed to preview barcodes: {str(e)}"
            )
    
    def _print_barcodes(self):
        """Print barcodes for selected devices"""
        selected_ids = self._get_selected_device_ids()
        if not selected_ids:
            MessageHandler.show_warning(
                self, 
                self.lm.get("Devices.no_selection", "No devices selected"), 
                self.lm.get("Devices.select_to_print", "Please select devices to print barcodes.")
            )
            return
        
        try:
            from utils.print.barcode_generator import BarcodeGenerator
            
            # Get device details with ticket numbers
            devices = []
            for device_id in selected_ids:
                device = self.device_controller.get_device(device_id)
                if device:
                    # Get the latest ticket for this device
                    try:
                        from models.ticket import Ticket
                        latest_ticket = Ticket.select().where(
                            (Ticket.device == device_id) & 
                            (Ticket.is_deleted == False)
                        ).order_by(Ticket.created_at.desc()).first()
                        
                        if latest_ticket:
                            # Add ticket number as attribute to device DTO
                            device.ticket_number = latest_ticket.ticket_number
                    except Exception as e:
                        print(f"Error fetching ticket for device {device_id}: {e}")
                    
                    devices.append(device)
            
            if not devices:
                MessageHandler.show_warning(
                    self,
                    self.lm.get("Common.error", "Error"),
                    "No valid devices found."
                )
                return
            
            # Print directly
            generator = BarcodeGenerator(self)
            result = generator.print_barcodes(devices)
            if result:
                MessageHandler.show_info(
                    self,
                    self.lm.get("Common.success", "Success"),
                    self.lm.get("Devices.print_opened", "Print document opened. Ready for thermal printer.")
                )
            # Don't show error if user cancels (result is False but no exception)
            
        except ImportError:
            MessageHandler.show_error(
                self,
                self.lm.get("Common.error", "Error"),
                "Required libraries missing. Install with: pip install weasyprint python-barcode"
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            MessageHandler.show_error(
                self,
                self.lm.get("Common.error", "Error"),
                f"Failed to print barcodes: {str(e)}"
            )
    
    def _export_to_csv(self):
        """Export devices to CSV"""
        try:
            import csv
            from PySide6.QtWidgets import QFileDialog
            from datetime import datetime
            
            # Get current devices based on filters
            devices = getattr(self, '_current_device_list', [])
            
            if not devices:
                MessageHandler.show_warning(
                    self, 
                    self.lm.get("Devices.no_devices", "No Devices"), 
                    self.lm.get("Devices.no_devices_export", "No devices to export.")
                )
                return
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                self.lm.get("Common.export_csv", "Export CSV"), 
                f"devices_export_{datetime.now().strftime('%Y%m%d')}.csv", 
                "CSV Files (*.csv)"
            )
            
            if not file_path:
                return
                
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['ID', 'Barcode', 'Brand', 'Model', 'Color', 'IMEI', 'Serial', 'Status', 'Customer']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for device in devices:
                    writer.writerow({
                        'ID': device.id,
                        'Barcode': device.barcode or '',
                        'Brand': device.brand or '',
                        'Model': device.model or '',
                        'Color': device.color or '',
                        'IMEI': device.imei or '',
                        'Serial': device.serial_number or '',
                        'Status': device.status.upper(),
                        'Customer': device.customer_name or ''
                    })
                    
            MessageHandler.show_info(
                self, 
                self.lm.get("Common.success", "Success"), 
                f"{self.lm.get('Common.export_success', 'Successfully exported')} {len(devices)} {self.lm.get('MainWindow.devices', 'devices')}."
            )
            
        except Exception as e:
            MessageHandler.show_error(
                self, 
                self.lm.get("Common.error", "Error"), 
                f"{self.lm.get('Common.export_failed', 'Failed to export')}: {str(e)}"
            )

    def _export_to_pdf(self):
        """Export devices to PDF report using WeasyPrint"""
        try:
            from PySide6.QtWidgets import QFileDialog
            import os
            import platform
            from datetime import datetime
            
            # Get current devices based on filters
            devices = getattr(self, '_current_device_list', [])
            
            if not devices:
                MessageHandler.show_warning(
                    self, 
                    self.lm.get("Devices.no_devices", "No Devices"), 
                    self.lm.get("Devices.no_devices_export", "No devices to export.")
                )
                return
            
            path, _ = QFileDialog.getSaveFileName(
                self, 
                self.lm.get("Common.export_pdf", "Save PDF"), 
                f"devices_report_{datetime.now().strftime('%Y%m%d')}.pdf", 
                "PDF Files (*.pdf)"
            )
            
            if not path:
                return
            
            # MacOS Fix for WeasyPrint
            if platform.system() == 'Darwin':
                os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = '/opt/homebrew/lib:/usr/local/lib:/usr/lib:' + os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')
                
            from weasyprint import HTML, CSS
            
            # Use fonts that support Burmese
            font_family = "'Myanmar Text', 'Myanmar MN', 'Noto Sans Myanmar', 'Pyidaungsu', sans-serif"
            
            html = f"""
            <html>
            <head>
                <style>
                    @page {{ size: A4 landscape; margin: 15mm; }}
                    body {{ font-family: {font_family}; }}
                    h1 {{ color: #2980B9; margin-bottom: 5px; }}
                    .meta {{ font-size: 10pt; color: #7F8C8D; margin-bottom: 20px; }}
                    
                    /* Summary Boxes */
                    .summary-container {{ display: flex; gap: 20px; margin-bottom: 20px; }}
                    .summary-box {{ 
                        border: 1px solid #BDC3C7; 
                        padding: 10px; 
                        width: 200px;
                        background-color: #ECF0F1;
                        border-radius: 4px;
                    }}
                    .summary-label {{ font-size: 9pt; color: #7F8C8D; }}
                    .summary-value {{ font-size: 11pt; font-weight: bold; color: #2C3E50; }}
                    
                    /* Table */
                    table {{ width: 100%; border-collapse: collapse; font-size: 9pt; }}
                    th {{ 
                        background-color: #3498DB; 
                        color: white; 
                        padding: 8px; 
                        text-align: left; 
                        border: 1px solid #2980B9;
                    }}
                    td {{ 
                        padding: 6px; 
                        border: 1px solid #BDC3C7; 
                        color: #2C3E50;
                    }}
                    tr:nth-child(even) {{ background-color: #F8F9F9; }}
                    
                    /* Status Colors */
                    .status-received {{ color: #4169E1; }}
                    .status-diagnosed {{ color: #20B2AA; }}
                    .status-repairing {{ color: #E67E22; }}
                    .status-repaired {{ color: #BA55D3; }}
                    .status-completed {{ color: #27AE60; font-weight: bold; }}
                    .status-returned {{ color: #2C3E50; font-style: italic; }}
                </style>
            </head>
            <body>
                <h1>{self.lm.get("Devices.report_title", "DEVICES REPORT")}</h1>
                <div class="meta">{self.lm.get("Common.generated", "Generated")}: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
            """
            
            # Calculate Summary
            status_counts = {}
            for d in devices:
                status = d.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Add Summary Section
            html += f"""
                <div class="summary-container">
                    <div class="summary-box">
                        <div class="summary-label">{self.lm.get("Devices.total_devices", "Total Devices")}</div>
                        <div class="summary-value">{len(devices)}</div>
                    </div>
                     <div class="summary-box">
                        <div class="summary-label">{self.lm.get("Common.received", "Received")}</div>
                        <div class="summary-value" style="color: #4169E1;">{status_counts.get('received', 0)}</div>
                    </div>
                     <div class="summary-box">
                        <div class="summary-label">{self.lm.get("Common.in_progress", "In Progress")}</div>
                        <div class="summary-value" style="color: #E67E22;">
                            {status_counts.get('diagnosed', 0) + status_counts.get('repairing', 0)}
                        </div>
                    </div>
                     <div class="summary-box">
                        <div class="summary-label">{self.lm.get("Common.completed", "Completed")}</div>
                        <div class="summary-value" style="color: #27AE60;">
                            {status_counts.get('repaired', 0) + status_counts.get('completed', 0)}
                        </div>
                    </div>
                </div>
            """
            
            # Table Header
            html += f"""
                <table>
                    <thead>
                        <tr>
                            <th>{self.lm.get("Inventory.barcode", "Barcode")}</th>
                            <th>{self.lm.get("Tickets.device_brand", "Brand")}</th>
                            <th>{self.lm.get("Tickets.device_model", "Model")}</th>
                            <th>{self.lm.get("Tickets.device_color", "Color")}</th>
                            <th>{self.lm.get("Tickets.device_imei", "IMEI")}</th>
                            <th>{self.lm.get("Tickets.device_serial", "Serial")}</th>
                            <th>{self.lm.get("Tickets.status", "Status")}</th>
                            <th>{self.lm.get("Tickets.customer", "Customer")}</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            # Table Rows
            for d in devices:
                status_text = self._get_localized_status(d.status).upper()
                status_class = f"status-{d.status.lower()}"
                
                html += f"""
                    <tr>
                        <td>{d.barcode or ''}</td>
                        <td>{d.brand or ''}</td>
                        <td>{d.model or ''}</td>
                        <td>{d.color or ''}</td>
                        <td>{d.imei or ''}</td>
                        <td>{d.serial_number or ''}</td>
                        <td class="{status_class}">{status_text}</td>
                        <td>{d.customer_name or ''}</td>
                    </tr>
                """
                
            html += f"""
                    </tbody>
                </table>
                <div style="margin-top: 20px; font-size: 8pt; color: #7F8C8D; border-top: 1px solid #BDC3C7; padding-top: 10px;">
                    {self.lm.get("Common.confidential_notice", "Confidential - For Internal Use Only")}
                </div>
            </body>
            </html>
            """
            
            HTML(string=html).write_pdf(path)
            
            # Try to open
            try:
                import subprocess
                if platform.system() == 'Darwin':       # macOS
                    subprocess.call(('open', path))
                elif platform.system() == 'Windows':    # Windows
                    os.startfile(path)
                else:                                   # Linux
                    subprocess.call(('xdg-open', path))
            except:
                pass

            MessageHandler.show_info(
                self,
                self.lm.get("Common.success", "Success"),
                f"{self.lm.get('Common.export_success', 'Successfully exported')} {len(devices)} {self.lm.get('MainWindow.devices', 'devices')}."
            )
            
        except ImportError:
             MessageHandler.show_error(
                self,
                self.lm.get("Common.error", "Error"),
                "WeasyPrint library not found. Please install: pip install weasyprint"
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            MessageHandler.show_error(
                self,
                self.lm.get("Common.error", "Error"),
                f"{self.lm.get('Common.export_failed', 'Failed to export to PDF')}: {str(e)}"
            )

    def _on_device_changed(self, *args):
        """Handle device changes"""
        QTimer.singleShot(500, self._load_devices)

    def showEvent(self, event):
        """Lazy load data when tab is shown"""
        super().showEvent(event)
        if not self._data_loaded:
            # key: Use a timer to allow UI to render first
            QTimer.singleShot(100, self._load_initial_data)
            self._data_loaded = True
            
    def _load_initial_data(self):
        """Load initial data sequentially"""
        self._load_customers()
        self._load_devices()

    def _subscribe_to_events(self):
        """Subscribe to domain events"""
        EventBus.subscribe(DeviceCreatedEvent, self._handle_domain_event)
        EventBus.subscribe(DeviceUpdatedEvent, self._handle_domain_event)
        EventBus.subscribe(DeviceDeletedEvent, self._handle_domain_event)
        EventBus.subscribe(DeviceRestoredEvent, self._handle_domain_event)
        
        EventBus.subscribe(TicketCreatedEvent, self._handle_domain_event)
        EventBus.subscribe(TicketUpdatedEvent, self._handle_domain_event)
        EventBus.subscribe(TicketStatusChangedEvent, self._handle_domain_event)

    def _handle_domain_event(self, event):
        """Handle domain events"""
        # Debounce multiple events
        QTimer.singleShot(100, lambda: self._on_device_changed())

    def closeEvent(self, event):
        """Clean up resources"""
        self._unsubscribe_from_events()
        super().closeEvent(event)

    def _unsubscribe_from_events(self):
        """Unsubscribe from domain events"""
        events = [
            DeviceCreatedEvent, DeviceUpdatedEvent, DeviceDeletedEvent, DeviceRestoredEvent,
            TicketCreatedEvent, TicketUpdatedEvent, TicketStatusChangedEvent
        ]
        for event_type in events:
            EventBus.unsubscribe(event_type, self._handle_domain_event)
