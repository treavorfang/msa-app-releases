"""
Modern License History Dashboard with Cards and List View
"""
from PySide6.QtWidgets import (QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QTableWidget, QTableWidgetItem,
                              QLineEdit, QComboBox, QMessageBox, QFileDialog,
                              QHeaderView, QMenu, QFrame, QApplication, QScrollArea,
                              QGridLayout, QTextEdit, QGroupBox, QStackedWidget)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
import os
import csv
from datetime import datetime, timedelta

from core import LOGO_PATH
from core.firebase_manager import OnlineManager
from .styles import (DIALOG_STYLE, CARD_STYLE, COLORS, GROUP_BOX_STYLE,
                     CARD_BLUE, CARD_GREEN, CARD_ORANGE, CARD_PURPLE,
                     INPUT_STYLE, BUTTON_PRIMARY_STYLE, BUTTON_SECONDARY_STYLE, 
                     BUTTON_SUCCESS_STYLE, BUTTON_danger_STYLE, TABLE_STYLE)
from .online_activation_dialog import OnlineActivationDialog


class LicenseDetailDialog(QDialog):
    """Compact Dialog to show details of a license entry"""
    def __init__(self, data, headers, parent=None):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle("License Details")
        self.setMinimumSize(900, 500)
        self.setStyleSheet(DIALOG_STYLE + GROUP_BOX_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel(f"INVOICE: {data.get('Invoice Number', 'N/A')}")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #3b82f6;")
        header_layout.addWidget(title)
        
        date_lbl = QLabel(f"Generated: {data.get('Generated Date', 'N/A')}")
        date_lbl.setStyleSheet("color: #94a3b8; font-size: 13px;")
        header_layout.addWidget(date_lbl)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Main Grid Content (2x2)
        # Main Grid Content (2x1) - Simplified
        grid = QGridLayout()
        grid.setSpacing(15)
        
        # 1. Customer Info (Top Left)
        grid.addWidget(self._create_customer_group(), 0, 0)
        
        # 2. License Info (Top Right)
        grid.addWidget(self._create_license_group(), 0, 1)
        
        # 3. Notes (Bottom Full Width)
        grid.addWidget(self._create_notes_group(), 1, 0, 1, 2)
        
        layout.addLayout(grid)
        
        # Footer Actions
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(100, 36)
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(100, 36)
        close_btn.setStyleSheet(BUTTON_PRIMARY_STYLE)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)

    def _create_customer_group(self):
        group = QGroupBox("CUSTOMER INFO")
        layout = QGridLayout()
        layout.setSpacing(8)
        
        fields = [
            ("Name", "Customer Name"),
            ("Email", "Email"),
            ("Phone", "Phone"),
            ("Location", "City") # Combo of City/Country? Just City for compact
        ]
        
        for i, (label, key) in enumerate(fields):
            self._add_row(layout, i, label, key)
            
        group.setLayout(layout)
        return group

    def _create_license_group(self):
        group = QGroupBox("LICENSE INFO")
        layout = QGridLayout()
        layout.setSpacing(8)
        
        fields = [
            ("Type", "License Type"),
            ("Expiry", "Expiry Date"),
            ("HWID", "HWID"),
            ("Renewal", "Renewal Reminder")
        ]
        
        for i, (label, key) in enumerate(fields):
            self._add_row(layout, i, label, key)
            
        group.setLayout(layout)
        return group

    def _create_payment_group(self):
        group = QGroupBox("PAYMENT INFO")
        layout = QGridLayout()
        layout.setSpacing(8)
        
        fields = [
            ("Amount", "Amount"),
            ("Method", "Payment Method"),
            ("Status", "Payment Status"),
            ("Inv. #", "Invoice Number")
        ]
        
        for i, (label, key) in enumerate(fields):
            self._add_row(layout, i, label, key)
            
        group.setLayout(layout)
        return group

    def _create_notes_group(self):
        group = QGroupBox("NOTES")
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        # Notes
        notes_val = str(self.data.get("Notes", "No notes available"))
        lbl = QLabel(notes_val)
        lbl.setStyleSheet("color: #94a3b8; font-style: italic;")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        
        group.setLayout(layout)
        return group

    def _add_row(self, layout, row, label_text, key):
        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #94a3b8; font-weight: bold;")
        layout.addWidget(lbl, row, 0)
        
        val_text = str(self.data.get(key, "-"))
        
        # Colorize Expiry or Status if needed
        val_lbl = QLabel(val_text)
        val_lbl.setStyleSheet("color: #e2e8f0;")
        val_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        if key == "Expiry Date":
             if "Expired" in self.data.get("Status", ""): # If we had status in data
                 val_lbl.setStyleSheet("color: #ef4444; font-weight: bold;")
        
        layout.addWidget(val_lbl, row, 1)

    def _copy_key(self):
        key = self.data.get("License Key", "")
        if key:
            QApplication.clipboard().setText(key)
            # Make the button flash or change text momentarily? 
            # Simple message box is annoying in detail view, just maybe silent or change btn text?
            # Let's show a small tooltip or just status.
            # Since we don't have a status bar in dialog, a quick MsgBox is safer.
            QMessageBox.information(self, "Copied", "License key copied!")


class CustomerDetailDialog(QDialog):
    """View details for a specific customer and their licenses"""
    def __init__(self, customer, parent=None):
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle(f"Customer: {customer['name']}")
        self.setMinimumSize(900, 600)
        self.setStyleSheet(DIALOG_STYLE)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24,24,24,24)
        
        # Header Info
        header = QHBoxLayout()
        # Profile Icon
        icon = QLabel("👤")
        icon.setStyleSheet("font-size: 48px; background: #334155; border-radius: 32px; padding: 8px;")
        icon.setFixedSize(70, 70)
        icon.setAlignment(Qt.AlignCenter)
        header.addWidget(icon)
        
        # Text Info
        info = QVBoxLayout()
        info.setSpacing(5)
        # Custom Header with Status
        name_layout = QHBoxLayout()
        name_lbl = QLabel(self.customer['name'])
        name_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        
        status_txt = self.customer.get('status', 'pending').upper()
        status_bg = "#f59e0b" # Orange
        if status_txt == "ACTIVE": status_bg = "#10b981" # Green
        elif status_txt == "SUSPENDED": status_bg = "#ef4444" # Red
        
        status_badge = QLabel(f"  {status_txt}  ")
        status_badge.setStyleSheet(f"background-color: {status_bg}; color: white; border-radius: 4px; font-weight: bold; font-size: 11px;")
        status_badge.setFixedHeight(22)
        
        name_layout.addWidget(name_lbl)
        name_layout.addWidget(status_badge)
        name_layout.addStretch()
        
        details = QLabel(f"📞 {self.customer.get('phone','N/A')} | 📧 {self.customer.get('email', 'N/A')}")
        details.setStyleSheet("color: #94a3b8; font-size: 14px;")
        
        loc = QLabel(f"📍 {self.customer.get('city','')} - {self.customer.get('country','')}")
        loc.setStyleSheet("color: #94a3b8; font-size: 13px;")
        
        info.addLayout(name_layout)
        info.addWidget(details)
        info.addWidget(loc)
        header.addLayout(info)
        header.addStretch()
        
        # Stats
        stats = QVBoxLayout()
        stats.setAlignment(Qt.AlignRight)
        
        dev_count = len(self.customer['licenses'])
        s1 = QLabel(f"Devices: {dev_count}")
        s1.setStyleSheet("font-size: 16px; font-weight: bold; color: #3b82f6;")
        
        spent_txt = f"{self.customer['total_spent_mmk']:,} Ks"
        if self.customer['total_spent_usd'] > 0:
            spent_txt += f" + ${self.customer['total_spent_usd']:,.2f}"
            
        s2 = QLabel(f"Total Revenue: {spent_txt}")
        s2.setStyleSheet("font-size: 14px; color: #10b981; font-weight: bold;")
        s2.setAlignment(Qt.AlignRight)
        
        stats.addWidget(s1)
        stats.addWidget(s2)
        header.addLayout(stats)
        
        layout.addLayout(header)
        
        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background: #334155; max-height: 1px;")
        layout.addWidget(line)
        
        # Licenses Table
        lbl = QLabel("Active Licenses & Devices")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #e2e8f0;")
        layout.addWidget(lbl)
        
        self.table = QTableWidget()
        self.table = QTableWidget()
        self.table.setStyleSheet(TABLE_STYLE)
        self._populate_table()
        # Enable context menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.cellDoubleClicked.connect(self._on_table_double_click)
        layout.addWidget(self.table)
        
        # Footer Actions
        footer = QHBoxLayout()
        
        # Action Buttons
        self.activate_btn = QPushButton("Approve User")
        self.activate_btn.clicked.connect(self._on_activate_clicked)
        self.activate_btn.setStyleSheet(BUTTON_SUCCESS_STYLE)
        
        self.suspend_btn = QPushButton("Suspend User")
        self.suspend_btn.clicked.connect(self._on_suspend_clicked)
        self.suspend_btn.setStyleSheet(BUTTON_danger_STYLE)

        self.renew_btn = QPushButton("Renew License")
        self.renew_btn.clicked.connect(self._on_renew_clicked)
        self.renew_btn.setStyleSheet(BUTTON_PRIMARY_STYLE)
        
        # Logic: Status based visibility
        st = self.customer.get('status', 'pending')
        
        # Add buttons in order
        footer.addWidget(self.activate_btn)
        footer.addWidget(self.suspend_btn)
        footer.addWidget(self.renew_btn)
        
        # Visibility Logic
        if st == 'active':
            self.activate_btn.setVisible(False)
        elif st == 'pending':
            self.suspend_btn.setVisible(False)
            self.renew_btn.setVisible(False)
        elif st == 'suspended':
            self.suspend_btn.setVisible(False)
            self.activate_btn.setText("Re-Activate")
            
        footer.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet(BUTTON_SECONDARY_STYLE)
        footer.addWidget(close_btn)
        
        layout.addLayout(footer)

    def _populate_table(self):
        cols = ["Generated", "HWID", "Type", "Status", "Expiry"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        
        self.sorted_licenses = sorted(self.customer['licenses'], key=lambda x: x.get('Generated Date', ''), reverse=True)
        self.table.setRowCount(len(self.sorted_licenses))
        
        for r, lic in enumerate(self.sorted_licenses):
            # Calculate Status
            status_txt = "Active"
            days = 0
            if 'Expiry Date' in lic:
                 try:
                     exp = datetime.strptime(lic['Expiry Date'], "%Y-%m-%d").date()
                     days = (exp - datetime.now().date()).days
                     if days < 0: status_txt = "Expired"
                     else: status_txt = f"{days} Days Left"
                 except: pass
            
            # 0: Generated
            self.table.setItem(r, 0, QTableWidgetItem(str(lic.get('Generated Date', ''))))
            # 1: HWID
            self.table.setItem(r, 1, QTableWidgetItem(str(lic.get('HWID', ''))[:20]+"..."))
            # 2: Type
            self.table.setItem(r, 2, QTableWidgetItem(str(lic.get('License Type', ''))))
            
            # 3: Status
            stat_item = QTableWidgetItem(status_txt)
            if days < 0: stat_item.setForeground(QColor('#ef4444'))
            else: stat_item.setForeground(QColor('#10b981'))
            self.table.setItem(r, 3, stat_item)
            
            # 4: Expiry
            self.table.setItem(r, 4, QTableWidgetItem(str(lic.get('Expiry Date', ''))))
            
        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(1, 150)

    def _get_selected_license(self):
        row = self.table.currentRow()
        if row >= 0 and row < len(self.sorted_licenses):
            return self.sorted_licenses[row]
        return None

    def _on_renew_clicked(self):
        lic = self._get_selected_license()
        if lic: self._open_renew(lic)
        else: QMessageBox.warning(self, "Select License", "Please select a license to renew.")

    def _show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item: return
        row = item.row()
        lic = self.sorted_licenses[row]
        
        menu.addAction("📄 View Details", lambda: self._on_table_double_click(row, 0))
        menu.addSeparator()
        menu.addAction("🔄 Renew Subscription", lambda: self._open_renew(lic))
        menu.addSeparator()
        # Updated per request: Remove redundant copies, add Save Invoice PDF
        menu.addAction("💾 Save Invoice PDF", lambda: self._save_invoice_pdf(lic))
        
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _calculate_renewal_reminder(self, expiry_str):
        if not expiry_str or expiry_str == 'N/A': return 'N/A'
        try:
            # Handle different formats if necessary, assuming YYYY-MM-DD
            exp_date = datetime.strptime(expiry_str, "%Y-%m-%d")
            reminder = exp_date - timedelta(days=30)
            return reminder.strftime("%Y-%m-%d")
        except:
            return 'N/A'

    def _save_invoice_pdf(self, lic_data):
        """Save the selected license/invoice as a PDF"""
        from core.license_invoice_generator import LicenseInvoiceGenerator
        
        # 1. Ask where to save
        filename = f"Invoice_{lic_data.get('Invoice Number', 'Draft')}.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Save Invoice", filename, "PDF Files (*.pdf)")
        if not path: return
        
        # 2. Prepare Data for Generator (Map keys)
        # LicenseInvoiceGenerator expects keys like 'invoice_number', 'amount', etc.
        # But 'lic_data' here (from table) has keys like 'Invoice Number', 'Amount'.
        data = {
            'invoice_number': lic_data.get('Invoice Number', 'N/A'),
            'generated_at': lic_data.get('Generated Date', datetime.now().strftime("%Y-%m-%d")),
            'license_type': lic_data.get('License Type', 'N/A'),
            'amount': lic_data.get('Amount', '0'),
            'payment_method': lic_data.get('Method', 'Cash'), # Assuming field rename if needed
            'hwid': lic_data.get('HWID', 'N/A'),
            'expiry_date': lic_data.get('Expiry Date', 'N/A'),
            'license_key': lic_data.get('License Key', 'N/A'),
            'status': lic_data.get('Status', 'Active'),
            
            # Enriched from Customer
            'customer_name': self.customer.get('name', 'N/A'),
            'email': self.customer.get('email', ''),
            'phone': self.customer.get('phone', ''),
            'note': lic_data.get('Notes', ''),
            'renewal_reminder': self._calculate_renewal_reminder(lic_data.get('Expiry Date'))
        }

        try:
             generator = LicenseInvoiceGenerator()
             generator.generate_pdf(data, path)
             QMessageBox.information(self, "Success", f"Invoice saved using WeasyPrint to:\n{path}")
        except Exception as e:
             QMessageBox.critical(self, "Error", f"Failed to generate PDF: {str(e)}")
        
    def _on_table_double_click(self, row, col):
        if row >= 0 and row < len(self.sorted_licenses):
            lic = self.sorted_licenses[row]
            # Show the detailed License Dialog
            # We can map keys from licenses dict to LicenseDetailDialog expectations
            # LicenseDetailDialog expects flat dict. 'lic' is mostly there but keys might differ.
            # Let's check LicenseDetailDialog keys: 'Invoice Number', 'Generated Date', 'Customer Name', 'License Key'
            
            # Need to enrich 'lic' with customer data if missing
            full_data = lic.copy()
            full_data['Customer Name'] = self.customer.get('name')
            full_data['Email'] = self.customer.get('email')
            full_data['Phone'] = self.customer.get('phone')
            full_data['City'] = self.customer.get('city')
            
            dlg = LicenseDetailDialog(full_data, [], self)
            dlg.exec()

    def _copy_txt(self, text):
        if text:
            QApplication.clipboard().setText(str(text))

    def _open_renew(self, data):
        """Open renewal/subscription dialog and update Firebase"""
        # We ignore 'data' (the license dict) and use self.customer (with ID)
        # Prepare fresh data including HWID if not present
        data = self.customer.copy()
        # Ensure HWID is passed. It might be in 'licenses' list or top level depending on parse
        if 'hwid' not in data and data.get('licenses'):
             data['hwid'] = data['licenses'][0].get('HWID', 'N/A')
             
        dlg = OnlineActivationDialog(data, self)
        dlg.setWindowTitle("Renew Subscription")
        # Optional: Set button text if dialog supports it, otherwise generic "Activate" is fine.
        
        if dlg.exec():
            res = dlg.result_data
            # Update Firebase
            # We access the manager via self.parent() if it's HistoryView
            manager = getattr(self.parent(), 'manager', None)
            if not manager:
                 # Fallback if parent isn't HistoryView (rare)
                 from core.firebase_manager import OnlineManager
                 manager = OnlineManager()
            
            if manager.update_status(self.customer['id'], 'active', res):
                QMessageBox.information(self, "Success", "Subscription Updated/Renewed successfully!")
                self.accept()
            else:
                 QMessageBox.critical(self, "Error", "Failed to update subscription in Firebase")
            
    def _on_activate_clicked(self):
        """Approve/Activate the user via Dialog"""
        from .online_activation_dialog import OnlineActivationDialog
        # Ensure HWID is passed
        data = self.customer.copy()
        if 'hwid' not in data and data.get('licenses'):
             data['hwid'] = data['licenses'][0].get('HWID', 'N/A')
             
        dlg = OnlineActivationDialog(data, self)
        if dlg.exec():
            res = dlg.result_data
            if self.parent().manager.update_status(self.customer['id'], 'active', res):
                QMessageBox.information(self, "Success", "User Activated")
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to update status")

    def _on_suspend_clicked(self):
        """Suspend the user"""
        ret = QMessageBox.warning(self, "Confirm Suspend", f"Are you sure you want to SUSPEND '{self.customer['name']}'?\nThey will not be able to login.", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            if self.parent().manager.update_status(self.customer['id'], 'suspended'):
                QMessageBox.information(self, "Success", "User Suspended")
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to update status")


class HistoryView(QWidget):
    """Modern Customer Dashboard (Customer View)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = OnlineManager()
        self.raw_data = [] # [Headers, Row, ...]
        self.customers = [] # List of grouped customer dicts
        self.filtered_customers = [] 
        
        self.stats_labels = {} 
        self.current_view = 'cards'
        
        self._setup_ui()
        self._refresh_data()
        
    def showEvent(self, event):
        """Auto-refresh on show"""
        self._refresh_data()
        super().showEvent(event)
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # --- Header ---
        header = QHBoxLayout()
        
        # Title
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        lbl_title = QLabel("Customer Dashboard")
        lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #e2e8f0;")
        lbl_desc = QLabel("Manage customers and licenses")
        lbl_desc.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_desc)
        header.addLayout(title_box)
        
        header.addStretch()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search customers...")
        self.search_input.setFixedWidth(280)
        self.search_input.setStyleSheet(INPUT_STYLE)
        self.search_input.textChanged.connect(self._on_search)
        header.addWidget(self.search_input)
        
        # View Switcher
        self.btn_cards = QPushButton("Cards")
        self.btn_list = QPushButton("List")
        
        btn_style = """
            QPushButton { background-color: #1e293b; border: 1px solid #334155; color: #94a3b8; border-radius: 6px; }
            QPushButton:checked { background-color: #3b82f6; color: white; border-color: #3b82f6; }
            QPushButton:hover { background-color: #273548; }
        """
        
        for btn in [self.btn_cards, self.btn_list]:
            btn.setCheckable(True)
            btn.setFixedSize(80, 36)
            btn.setCursor(Qt.PointingHandCursor)
            # Switcher needs custom style for toggling, but base can be secondary
            # Checkable logic might need inline or specific style
            btn.setStyleSheet("""
                QPushButton { background-color: #1e293b; border: 1px solid #334155; color: #94a3b8; border-radius: 6px; font-weight: bold; }
                QPushButton:checked { background-color: #3b82f6; color: white; border-color: #3b82f6; }
                QPushButton:hover { background-color: #273548; }
            """)
            
        self.btn_cards.clicked.connect(lambda: self._switch_view('cards'))
        self.btn_list.clicked.connect(lambda: self._switch_view('list'))
        
        header.addWidget(self.btn_cards)
        header.addWidget(self.btn_list)
        
        # Refresh
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedSize(80, 36)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self._refresh_data)
        refresh_btn.setStyleSheet(BUTTON_SECONDARY_STYLE)
        header.addWidget(refresh_btn)

        layout.addLayout(header)
        
        # --- Stats ---
        self._create_stats_bar(layout)
        
        # --- Content Stack ---
        self.stack = QStackedWidget()
        
        # 1. Cards View
        self.page_cards = QWidget()
        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setFrameShape(QFrame.NoFrame)
        self.cards_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent;")
        self.cards_grid = QGridLayout(self.cards_container)
        self.cards_grid.setSpacing(15)
        self.cards_grid.setContentsMargins(0,0,10,0)
        self.cards_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.cards_scroll.setWidget(self.cards_container)
        
        cards_layout = QVBoxLayout(self.page_cards)
        cards_layout.setContentsMargins(0,0,0,0)
        cards_layout.addWidget(self.cards_scroll)
        self.stack.addWidget(self.page_cards)
        
        # 2. List View (Table)
        self.page_list = QWidget()
        list_layout = QVBoxLayout(self.page_list)
        list_layout.setContentsMargins(0,0,0,0)
        
        self.table = QTableWidget()
        self._setup_table()
        list_layout.addWidget(self.table)
        
        self.stack.addWidget(self.page_list)
        
        layout.addWidget(self.stack)
        
        # Init View
        self._switch_view('cards')
        
    def _create_stats_bar(self, layout):
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        # Helpers
        def _card(key, title, icon, color_style):
            frame = QFrame()
            frame.setStyleSheet(color_style)
            frame.setFixedHeight(100)
            l = QHBoxLayout(frame)
            l.setContentsMargins(20, 15, 20, 15)
            
            v = QVBoxLayout()
            t = QLabel(title)
            t.setStyleSheet("color: #e2e8f0; font-weight: bold; font-size: 11px; background-color: transparent;")
            val = QLabel("0")
            val.setStyleSheet("font-size: 24px; font-weight: bold; color: white; background-color: transparent;")
            self.stats_labels[key] = val
            v.addWidget(t)
            v.addWidget(val)
            l.addLayout(v)
            l.addStretch()
            
            ic = QLabel(icon)
            ic.setStyleSheet("font-size: 36px; background: transparent;")
            l.addWidget(ic)
            return frame
            
        cards_layout.addWidget(_card("TOTAL", "TOTAL CUSTOMERS", "👥", CARD_BLUE))
        cards_layout.addWidget(_card("ACTIVE", "ACTIVE DEVICES", "✅", CARD_GREEN))
        cards_layout.addWidget(_card("REV_MMK", "REVENUE (MMK)", "🇲🇲", CARD_PURPLE))
        cards_layout.addWidget(_card("REV_USD", "REVENUE (USD)", "💵", CARD_ORANGE))
        
        layout.addLayout(cards_layout)
        
    def _switch_view(self, mode):
        self.current_view = mode
        self.btn_cards.setChecked(mode == 'cards')
        self.btn_list.setChecked(mode == 'list')
        
        if mode == 'cards':
            self.stack.setCurrentWidget(self.page_cards)
            self._render_cards()
        else:
            self.stack.setCurrentWidget(self.page_list)
            self._render_list()

    def _load_data(self):
        """Load and parse data from Online Manager (Firebase)"""
        users = self.manager.get_users() # Returns list of dicts
        self.customers = [] 
        
        if not users:
            self.filtered_customers = []
            return
            
        # 1. Fetch Invoices and Group by User
        invoices = self.manager.get_invoices() # List of dicts
        user_invoices = {}
        for inv in invoices:
            uid = inv.get('user_email')
            if uid:
                uid = uid.strip().lower() # Normalize
                if uid not in user_invoices: user_invoices[uid] = []
                user_invoices[uid].append(inv)
            
        # Map Firebase Users to Dashboard Customer Structure
        for user in users:
             user_id = user.get('id', '').strip().lower()
             
             # Calculate spent from TIED invoices
             mmk = 0
             usd = 0.0
             
             my_invoices = user_invoices.get(user_id, [])
             
             # Determine Latest Invoice for displayed details
             latest_inv = {}
             if my_invoices:
                 # Sort by created_at desc just in case
                 # (get_invoices already sorted but local sort is safer for subset)
                 # We assume my_invoices is already in order from get_invoices or we pick first
                 latest_inv = my_invoices[0]
                 
             for inv in my_invoices:
                 amt_str = str(inv.get('amount', '0'))
                 try:
                     if 'MMK' in amt_str:
                         mmk += int(float(amt_str.replace('MMK','').replace(',','').strip()))
                     elif 'USD' in amt_str or '$' in amt_str:
                         usd += float(amt_str.replace('USD','').replace('$','').strip())
                 except: pass

             # Map License Data
             # We treat the current user state as their "License"
             # Use fields from Latest Invoice if available, else fallbacks
             license_entry = {
                 'Generated Date': latest_inv.get('created_at', user.get('activated_at', user.get('created_at', ''))),
                 'HWID': user.get('hwid', ''),
                 'License Type': user.get('license_type', 'Standard'),
                 'Status': user.get('status', 'unknown'),
                 'Invoice Number': latest_inv.get('invoice_number', 'N/A'),
                 'Expiry Date': user.get('expiration_date', ''),
                 'Amount': latest_inv.get('amount', '0'),
                 'Method': latest_inv.get('payment_method', ''),
                 'Payment Status': latest_inv.get('payment_status', ''),
                 'Notes': user.get('notes', ''),
                 'Renewal Reminder': user.get('renewal_reminder', '-'),
                 'License Key': user.get('license_key', '') 
             }

             customer = {
                 'id': user.get('id'), # Firebase Doc ID
                 'status': user.get('status', 'pending'),
                 'name': user.get('name', 'Unknown User'),
                 'phone': user.get('phone', ''),
                 'email': user.get('email', ''),
                 'city': user.get('city', ''),
                 'country': user.get('country', ''),
                 'licenses': [license_entry], # List of 1 for now
                 'total_spent_mmk': mmk,
                 'total_spent_usd': usd,
                 'last_updated': datetime.now() # Placeholder or parse 'created_at'
             }
             
             # Parse actual date for sorting
             try:
                 txt = user.get('created_at', '')
                 if txt:
                     pass 
             except: pass

             self.customers.append(customer)
             
        self.filtered_customers = self.customers

    def _refresh_data(self):
        self._load_data()
        self._update_stats()
        self._on_search() 

    def _on_search(self):
        text = self.search_input.text().lower().strip()
        if not text:
            self.filtered_customers = list(self.customers)
        else:
            self.filtered_customers = [
                c for c in self.customers 
                if text in c['name'].lower() or text in str(c.get('phone','')).lower()
            ]
        
        if self.current_view == 'cards':
            self._render_cards()
        else:
            self._render_list()

    def _render_cards(self):
        # Clear grid
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        # Populate
        cols = 3
        for idx, cust in enumerate(self.filtered_customers):
            row, col = divmod(idx, cols)
            card = self._create_customer_card(cust)
            self.cards_grid.addWidget(card, row, col)

    def _create_customer_card(self, data):
        frame = QFrame()
        frame.setFixedSize(280, 160)
        frame.setCursor(Qt.PointingHandCursor)
        
        frame.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 12px;
            }
            QFrame:hover {
                background-color: #273548;
                border-color: #3b82f6;
            }
        """)
        
        # Mouse Events for Detail
        def mousePressEvent(e):
             if e.button() == Qt.LeftButton:
                 self._open_detail(data)
             elif e.button() == Qt.RightButton:
                 self._show_customer_context_menu(data, e.globalPos())
                 
        frame.mousePressEvent = mousePressEvent
        
        # Layout
        layout = QVBoxLayout(frame)
        layout.setSpacing(5)
        
        # Top: Name + Badges
        top = QHBoxLayout()
        name = QLabel(data['name'][:18])
        name.setStyleSheet("font-weight: bold; font-size: 14px; color: white; border: none; background: transparent;")
        top.addWidget(name)
        top.addStretch()
        
        # Status Badge
        status_txt = data.get('status', 'pending').upper()
        status_bg = "#f59e0b" # Orange
        if status_txt == "ACTIVE": status_bg = "#10b981" # Green
        elif status_txt == "SUSPENDED": status_bg = "#ef4444" # Red
        
        st_badge = QLabel(f"{status_txt}")
        st_badge.setStyleSheet(f"background-color: {status_bg}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; border: none;")
        top.addWidget(st_badge)

        dev_count = len(data['licenses'])
        badge = QLabel(f"{dev_count} Device{'s' if dev_count>1 else ''}")
        badge.setStyleSheet("color: white; background-color: #3b82f6; padding: 2px 6px; border-radius: 4px; font-size: 10px; border: none;")
        top.addWidget(badge)
        layout.addLayout(top)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #334155; height: 1px; border: none;")
        layout.addWidget(line)
        
        # Details
        def _row(icon, txt):
            r = QHBoxLayout()
            i = QLabel(icon)
            i.setStyleSheet("color: #94a3b8; font-size: 12px; border: none; background: transparent;")
            l = QLabel(txt)
            l.setStyleSheet("color: #cbd5e1; font-size: 12px; border: none; background: transparent;")
            r.addWidget(i)
            r.addWidget(l)
            r.addStretch()
            return r
            
        layout.addLayout(_row("📞", data.get('phone', 'N/A')))
        layout.addLayout(_row("📍", f"{data.get('city','')}"))
        
        # Revenue
        spent = f"{data['total_spent_mmk']:,} Ks"
        if data['total_spent_usd'] > 0:
            spent = f"${data['total_spent_usd']:,.2f}" # Prioritize USD or show mixed? Space limited.
        layout.addLayout(_row("💰", spent))
        
        layout.addStretch()
        return frame

    def _setup_table(self):
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #1e293b; color: #e2e8f0; border: none; border-radius: 8px; font-size: 13px; }
            QHeaderView::section { background-color: #0f172a; color: #94a3b8; padding: 10px; border: none; font-weight: bold; }
            QTableWidget::item { padding: 6px; border-bottom: 1px solid #334155; }
        """)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_list_context_menu)
        self.table.cellDoubleClicked.connect(lambda r, c: self._open_detail(self.filtered_customers[r]))

    def _render_list(self):
        cols = ["Customer Name", "Phone", "Devices", "Last Activity", "Total Spent"]
        self.table.clear()
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.setRowCount(len(self.filtered_customers))
        
        for r, data in enumerate(self.filtered_customers):
            # Name
            self.table.setItem(r, 0, QTableWidgetItem(str(data['name'])))
            # Phone
            self.table.setItem(r, 1, QTableWidgetItem(str(data.get('phone',''))))
            # Devices
            self.table.setItem(r, 2, QTableWidgetItem(str(len(data['licenses']))))
            # Last Activity
            last_act = data['last_updated'].strftime("%Y-%m-%d") if data['last_updated'] != datetime.min else ""
            self.table.setItem(r, 3, QTableWidgetItem(last_act))
            # Spent
            spent = f"{data['total_spent_mmk']:,} Ks"
            if data['total_spent_usd'] > 0: spent += f" / ${data['total_spent_usd']:,.2f}"
            self.table.setItem(r, 4, QTableWidgetItem(spent))
            
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

    def _open_detail(self, data):
        dlg = CustomerDetailDialog(data, self)
        # If dialog closes, refresh in case they renewed/deleted something
        if dlg.exec(): 
            self._refresh_data()
        else:
            self._refresh_data() # Refresh anyway
    
    def _export_csv(self):
        # Simplified export of current filtered licenses
        path, _ = QFileDialog.getSaveFileName(self, "Export", "history.csv", "CSV (*.csv)")
        if path:
            try:
                # We need to flatten our groups back to list
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if self.raw_data:
                        writer.writerow(self.raw_data[0]) # Headers
                        for cust in self.filtered_customers:
                            for lic in cust['licenses']:
                                # Reconstruct row
                                row = [lic.get(h, "") for h in self.raw_data[0]]
                                writer.writerow(row)
                QMessageBox.information(self, "Success", f"Exported to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _update_stats(self):
        total_customers = len(self.customers)
        active_licenses = 0
        mmk = 0
        usd = 0.0
        
        for cust in self.customers:
            # active += sum(1 for l in cust['licenses'] if self._is_active(l)) 
            for l in cust['licenses']:
                if self._is_active(l): active_licenses += 1
            
            mmk += cust['total_spent_mmk']
            usd += cust['total_spent_usd']
            
        if "TOTAL" in self.stats_labels: self.stats_labels["TOTAL"].setText(str(total_customers))
        if "ACTIVE" in self.stats_labels: self.stats_labels["ACTIVE"].setText(str(active_licenses))
        if "REV_MMK" in self.stats_labels: self.stats_labels["REV_MMK"].setText(f"{mmk:,} Ks")
        if "REV_USD" in self.stats_labels: self.stats_labels["REV_USD"].setText(f"${usd:,.2f}")

    def _is_active(self, lic):
        if 'Expiry Date' not in lic: return True
        try:
             exp = datetime.strptime(lic['Expiry Date'], "%Y-%m-%d").date()
             return exp >= datetime.now().date()
        except: return False

    def _show_customer_context_menu(self, data, pos):
        """Right click menu for customer (Shared by Card/List)"""
        menu = QMenu(self)
        
        # Open Detail
        menu.addAction("📄 View Details", lambda: self._open_detail(data))
        
        status = data.get('status', 'pending')
        doc_id = data.get('id')
        
        # Approve / Suspend
        if status == 'pending':
            menu.addAction("✅ Approve User", lambda: self._open_activation_dialog(data))
        elif status == 'active':
            menu.addAction("⛔ Suspend User", lambda: self._update_status(data, 'suspended'))
        elif status == 'suspended':
            menu.addAction("✅ Re-Activate User", lambda: self._open_activation_dialog(data))

        menu.addSeparator()
        
        # Copy Contact
        menu.addAction("📋 Copy Email", lambda: self._copy_text(data.get('email')))
        menu.addAction("📞 Copy Phone", lambda: self._copy_text(data.get('phone')))
        
        menu.addSeparator()
        menu.addAction("🗑 Delete User", lambda: self._delete_user(data))
        
        menu.exec(pos)

    def _show_list_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item: return
        row = item.row()
        if row < len(self.filtered_customers):
            data = self.filtered_customers[row]
            self._show_customer_context_menu(data, self.table.viewport().mapToGlobal(pos))

    def _copy_text(self, text):
        if text:
            QApplication.clipboard().setText(str(text))
            
    def _update_status(self, data, new_status):
        if self.manager.update_status(data['id'], new_status):
            QMessageBox.information(self, "Success", f"User marked as {new_status}")
            self._refresh_data()
        else:
            QMessageBox.critical(self, "Error", "Failed to update status")

    def _delete_user(self, data):
        confirm = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete '{data['name']}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            if self.manager.delete_user(data['id']):
                self._refresh_data()
            else:
                 QMessageBox.critical(self, "Error", "Failed to delete user")

    def _open_activation_dialog(self, data):
        """Open the activation dialog to collect plan details"""
        dlg = OnlineActivationDialog(data, self)
        if dlg.exec():
            result = dlg.result_data
            if self.manager.update_status(data['id'], 'active', result):
                QMessageBox.information(self, "Success", "User activated successfully!")
                self._refresh_data()
            else:
                QMessageBox.critical(self, "Error", "Failed to update user status.")






