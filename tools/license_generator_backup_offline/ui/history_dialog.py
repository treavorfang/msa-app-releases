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
from datetime import datetime

from core import HistoryManager, LOGO_PATH
from .styles import (DIALOG_STYLE, CARD_STYLE, COLORS, GROUP_BOX_STYLE,
                     CARD_BLUE, CARD_GREEN, CARD_ORANGE, CARD_PURPLE)


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
        grid = QGridLayout()
        grid.setSpacing(15)
        
        # 1. Customer Info (Top Left)
        grid.addWidget(self._create_customer_group(), 0, 0)
        
        # 2. License Info (Top Right)
        grid.addWidget(self._create_license_group(), 0, 1)
        
        # 3. Payment Info (Bottom Left)
        grid.addWidget(self._create_payment_group(), 1, 0)
        
        # 4. Key & Notes (Bottom Right)
        grid.addWidget(self._create_key_group(), 1, 1)
        
        layout.addLayout(grid)
        
        # Footer Actions
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        copy_btn = QPushButton("Copy Key")
        copy_btn.setFixedSize(100, 36)
        copy_btn.setStyleSheet("""
            QPushButton { background-color: #334155; border: 1px solid #475569; border-radius: 6px; color: white; font-weight: bold; }
            QPushButton:hover { background-color: #475569; }
        """)
        copy_btn.clicked.connect(self._copy_key)
        btn_layout.addWidget(copy_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(100, 36)
        close_btn.setStyleSheet("""
            QPushButton { background-color: #3b82f6; border-radius: 6px; font-weight: bold; color: white; border: none;}
            QPushButton:hover { background-color: #2563eb; }
        """)
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

    def _create_key_group(self):
        group = QGroupBox("KEY & NOTES")
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        # Notes
        notes_val = str(self.data.get("Notes", ""))
        if notes_val:
            lbl = QLabel(f"Notes: {notes_val}")
            lbl.setStyleSheet("color: #94a3b8; font-style: italic;")
            layout.addWidget(lbl)
        
        # Key
        key_edit = QTextEdit(str(self.data.get("License Key", "")))
        key_edit.setReadOnly(True)
        key_edit.setStyleSheet("background-color: #1e293b; border: 1px solid #475569; border-radius: 4px; padding: 5px; font-family: Menlo, Monaco, Consolas, monospace; font-size: 11px;")
        layout.addWidget(key_edit)
        
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
        name = QLabel(self.customer['name'])
        name.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        
        details = QLabel(f"📞 {self.customer.get('phone','N/A')} | 📧 {self.customer.get('email', 'N/A')}")
        details.setStyleSheet("color: #94a3b8; font-size: 14px;")
        
        loc = QLabel(f"📍 {self.customer.get('city','')} - {self.customer.get('country','')}")
        loc.setStyleSheet("color: #94a3b8; font-size: 13px;")
        
        info.addWidget(name)
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
        self.table.setStyleSheet("""
            QTableWidget { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; color: #e2e8f0; gridline-color: #334155; }
            QHeaderView::section { background-color: #0f172a; padding: 10px; border: none; font-weight: bold; color: #94a3b8; }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #334155; }
            QTableWidget::item:selected { background-color: #3b82f6; }
        """)
        self._populate_table()
        # Enable context menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.table)
        
        # Footer Actions
        footer = QHBoxLayout()
        
        self.renew_btn = QPushButton("Renew License")
        self.renew_btn.clicked.connect(self._on_renew_clicked)
        self.renew_btn.setStyleSheet("background-color: #10b981; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("background-color: #334155; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        
        footer.addWidget(self.renew_btn)
        footer.addStretch()
        footer.addWidget(close_btn)
        layout.addLayout(footer)

    def _populate_table(self):
        cols = ["Generated", "HWID", "Type", "Status", "Invoice", "Expiry"]
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
            
            # 4: Invoice
            self.table.setItem(r, 4, QTableWidgetItem(str(lic.get('Invoice Number', ''))))
            # 5: Expiry
            self.table.setItem(r, 5, QTableWidgetItem(str(lic.get('Expiry Date', ''))))
            
            # Save data for row
            # We can use parallel list self.sorted_licenses since order is static
            
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
        
        menu = QMenu(self)
        menu.addAction("Renew License", lambda: self._open_renew(lic))
        menu.addAction("Copy License Key", lambda: self._copy_txt(lic.get('License Key')))
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _copy_txt(self, text):
        if text:
            QApplication.clipboard().setText(str(text))

    def _open_renew(self, data):
        dlg = RenewalDialog(data, self)
        if dlg.exec():
            # If renewed, we should ideally refresh this dialog or close it
            # But the accepted signal will propagate refresh to parent
            self.accept()


class HistoryView(QWidget):
    """Modern Customer Dashboard (Customer View)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_manager = HistoryManager()
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
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px 12px;
                color: white;
                font-size: 13px;
            }
            QLineEdit:focus { border-color: #3b82f6; }
        """)
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
            btn.setStyleSheet(btn_style)
            
        self.btn_cards.clicked.connect(lambda: self._switch_view('cards'))
        self.btn_list.clicked.connect(lambda: self._switch_view('list'))
        
        header.addWidget(self.btn_cards)
        header.addWidget(self.btn_list)
        
        # Refresh
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedSize(80, 36)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self._refresh_data)
        refresh_btn.setStyleSheet("""
            QPushButton { background-color: #334155; border-radius: 6px; color: white; font-weight: bold; border: none; }
            QPushButton:hover { background-color: #475569; }
        """)
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
        """Load and parse data"""
        self.raw_data = self.history_manager.load_history()
        self.customers = [] # Grouped customers
        
        if not self.raw_data:
            self.filtered_customers = []
            return
            
        headers = self.raw_data[0]
        customers_map = {}
        
        # Group by Name
        for row in self.raw_data[1:]:
             d = {}
             for i, h in enumerate(headers):
                 if i < len(row): d[h] = row[i]

             name = d.get('Customer Name', 'Unknown')
             if not name: name = 'Unknown'
             
             if name not in customers_map:
                 customers_map[name] = {
                     'name': name,
                     'phone': d.get('Phone', ''),
                     'email': d.get('Email', ''),
                     'city': d.get('City', ''),
                     'country': d.get('Country', ''),
                     'licenses': [],
                     'total_spent_mmk': 0,
                     'total_spent_usd': 0.0,
                     'last_updated': datetime.min
                 }
                 
             # Add license info
             customers_map[name]['licenses'].append(d)
             
             # Stats
             amt = str(d.get('Amount', ''))
             try:
                 if 'MMK' in amt:
                     customers_map[name]['total_spent_mmk'] += int(amt.replace('MMK','').replace(',','').strip())
                 elif 'USD' in amt or '$' in amt:
                     customers_map[name]['total_spent_usd'] += float(amt.replace('USD','').replace('$','').strip())
             except: pass
             
             # Update Date
             try:
                 gen_date = datetime.strptime(d.get('Generated Date', ''), "%Y-%m-%d %H:%M:%S")
                 if gen_date > customers_map[name]['last_updated']:
                     customers_map[name]['last_updated'] = gen_date
             except: pass

        self.customers = list(customers_map.values())
        # Sort by latest
        self.customers.sort(key=lambda x: x['last_updated'], reverse=True)
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
                 
        frame.mousePressEvent = mousePressEvent
        
        # Layout
        layout = QVBoxLayout(frame)
        layout.setSpacing(5)
        
        # Top: Name + Device Count Badge
        top = QHBoxLayout()
        name = QLabel(data['name'][:18])
        name.setStyleSheet("font-weight: bold; font-size: 14px; color: white; border: none; background: transparent;")
        top.addWidget(name)
        top.addStretch()
        
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



# ==========================================
# Renewal Dialog Helper Class
# ==========================================

from core import DEFAULT_DURATION_INDEX, DURATION_OPTIONS, CURRENCY_OPTIONS, PAYMENT_METHOD_OPTIONS, PRICING_MAP_MMK, PRICING_MAP_USD
from core.generator import LicenseGeneratorCore
from core.license_invoice_generator import LicenseInvoiceGenerator
from .styles import COMBOBOX_STYLE, GENERATE_BUTTON_STYLE

class RenewalDialog(QDialog):
    """Dialog to renew (generate new) license for existing customer"""
    def __init__(self, old_data, parent=None):
        super().__init__(parent)
        self.old_data = old_data
        self.generator = LicenseGeneratorCore()
        
        self.setWindowTitle("Renew License")
        self.setMinimumSize(400, 450)
        self.setStyleSheet(DIALOG_STYLE + COMBOBOX_STYLE + GENERATE_BUTTON_STYLE)
        
        self._setup_ui()
        self._load_defaults()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel(f"Renewing: {self.old_data.get('Customer Name', 'Unknown')}")
        header.setStyleSheet("color: #3b82f6; font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        sub_header = QLabel(f"HWID: {self.old_data.get('HWID', 'Unknown')}")
        sub_header.setStyleSheet("color: #94a3b8; font-size: 12px; font-family: Menlo, Monaco, Consolas, monospace;")
        layout.addWidget(sub_header)
        
        layout.addSpacing(10)
        
        # Form Grid
        grid = QGridLayout()
        grid.setSpacing(10)
        
        # Duration
        grid.addWidget(QLabel("Duration:"), 0, 0)
        self.duration_combo = QComboBox()
        for label, days in DURATION_OPTIONS:
            self.duration_combo.addItem(label, days)
        self.duration_combo.currentIndexChanged.connect(self._update_amount)
        grid.addWidget(self.duration_combo, 0, 1)
        
        # Currency
        grid.addWidget(QLabel("Currency:"), 1, 0)
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(CURRENCY_OPTIONS)
        self.currency_combo.currentIndexChanged.connect(self._update_amount)
        grid.addWidget(self.currency_combo, 1, 1)
        
        # Amount
        grid.addWidget(QLabel("Amount:"), 2, 0)
        self.amount_input = QLineEdit()
        self.amount_input.setReadOnly(False) # Allow manual override
        grid.addWidget(self.amount_input, 2, 1)
        
        # Payment Method
        grid.addWidget(QLabel("Payment:"), 3, 0)
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(PAYMENT_METHOD_OPTIONS)
        grid.addWidget(self.payment_combo, 3, 1)
        
        layout.addLayout(grid)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #334155;")
        cancel_btn.clicked.connect(self.reject)
        
        renew_btn = QPushButton("Generate Renewal")
        renew_btn.setStyleSheet("background-color: #10b981; font-weight: bold;")
        renew_btn.clicked.connect(self._generate_renewal)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(renew_btn)
        layout.addLayout(btn_layout)

    def _load_defaults(self):
        # Auto-select currency based on previous invoice amount string (e.g. "MMK 200,000")
        prev_amt = str(self.old_data.get('Amount', ''))
        if "MMK" in prev_amt:
            idx = self.currency_combo.findText("MMK")
            if idx >= 0: self.currency_combo.setCurrentIndex(idx)
        elif "$" in prev_amt or "USD" in prev_amt:
            idx = self.currency_combo.findText("USD")
            if idx >= 0: self.currency_combo.setCurrentIndex(idx)
            
        # Select default duration
        self.duration_combo.setCurrentIndex(DEFAULT_DURATION_INDEX)
        
        self._update_amount()

    def _update_amount(self):
        duration = self.duration_combo.currentText()
        currency = self.currency_combo.currentText()
        
        if currency == "MMK":
            price = PRICING_MAP_MMK.get(duration, 0)
            self.amount_input.setText(f"{price:,}")
        else:
            price = PRICING_MAP_USD.get(duration, 0)
            self.amount_input.setText(f"{price:.2f}")

    def _generate_renewal(self):
        try:
            # 1. Generate new key
            name = self.old_data.get('Customer Name', 'Unknown')
            hwid = self.old_data.get('HWID', '')
            days = self.duration_combo.currentData()
            
            if not hwid:
                QMessageBox.warning(self, "Error", "Cannot renew: Missing HWID")
                return

            new_data = self.generator.generate(name, hwid, days)
            
            # 2. Fill in other info
            currency = self.currency_combo.currentText()
            amt_val = self.amount_input.text()
            
            # Map old data fields to new standard fields
            new_data.update({
                'customer_name': name,
                'email': self.old_data.get('Email', ''),
                'phone': self.old_data.get('Phone', ''),
                'city': self.old_data.get('City', ''),
                'country': self.old_data.get('Country', ''),
                'license_type': self.duration_combo.currentText(),
                'invoice_number': f"REN-{datetime.now().strftime('%m%d-%H%M')}", 
                'amount': f"{currency} {amt_val}",
                'payment_method': self.payment_combo.currentText(),
                'payment_status': 'Paid', # Assume paid if renewing
                'notes': f"Renewed from previous license. Old invoice: {self.old_data.get('Invoice Number', 'N/A')}"
            })
            
            # 3. Save to DB
            history = HistoryManager()
            history.save_license(new_data)
            
            # 4. Generate Invoice
            invoice_gen = LicenseInvoiceGenerator()
            
            # Auto-save to Desktop
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            filename = f"License_Renewal_{new_data.get('invoice_number', 'INV')}.pdf"
            pdf_path = os.path.join(desktop, filename)
            
            invoice_gen.generate_pdf(new_data, pdf_path)
            
            QMessageBox.information(self, "Success", f"License Renewed!\n\nNew Key:\n{new_data['license_key']}\n\nInvoice Saved:\n{pdf_path}")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Renewal failed: {str(e)}")

