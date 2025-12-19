from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QPushButton, QHBoxLayout, QLabel, QMenu, QMessageBox, 
                               QFileDialog, QDateEdit, QFrame, QLineEdit, QComboBox, QGroupBox)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QTextDocument, QColor
from PySide6.QtPrintSupport import QPrinter
from core.firebase_manager import OnlineManager
from datetime import datetime
from .styles import (COMBOBOX_STYLE, INPUT_STYLE, TABLE_STYLE, 
                    BUTTON_PRIMARY_STYLE, BUTTON_SECONDARY_STYLE, GROUP_BOX_STYLE)

class InvoicesView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = OnlineManager()
        self.invoices = []
        self.filtered_invoices = []
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
        t = QLabel("Financial Records")
        t.setStyleSheet("font-size: 24px; font-weight: bold; color: #e2e8f0;")
        sub = QLabel("Track revenue and invoice history")
        sub.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(t)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        
        header.addStretch()
        
        # Search Bar (New)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Invoice #, Customer, Amount...")
        self.search_input.setFixedWidth(280)
        self.search_input.setStyleSheet(INPUT_STYLE)
        self.search_input.textChanged.connect(self._apply_filter) # Real-time search
        header.addWidget(self.search_input)
        
        header.addSpacing(10)
        
        # Toggle Advanced Filter
        self.adv_filter_btn = QPushButton("Filters ⚡") # Icon optional
        self.adv_filter_btn.setCheckable(True)
        self.adv_filter_btn.setChecked(False)
        self.adv_filter_btn.setCursor(Qt.PointingHandCursor)
        self.adv_filter_btn.toggled.connect(self._toggle_filter_panel)
        self.adv_filter_btn.setStyleSheet(BUTTON_SECONDARY_STYLE)
        header.addWidget(self.adv_filter_btn)
        
        # Export
        export_btn = QPushButton("Export CSV")
        export_btn.clicked.connect(self._export_csv)
        export_btn.setStyleSheet(BUTTON_SECONDARY_STYLE)
        header.addWidget(export_btn)
        
        # Refresh
        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("Refresh Data")
        refresh_btn.clicked.connect(self.refresh_data)
        refresh_btn.setFixedSize(36, 36)
        refresh_btn.setStyleSheet(BUTTON_SECONDARY_STYLE)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # --- Advanced Filter Panel (Collapsible) ---
        self.filter_frame = QFrame()
        self.filter_frame.setVisible(False) # Hidden by default
        self.filter_frame.setStyleSheet("background-color: #1e293b; border-radius: 8px; border: 1px solid #334155;")
        f_layout = QHBoxLayout(self.filter_frame)
        f_layout.setContentsMargins(15, 15, 15, 15)
        f_layout.setSpacing(15)
        
        # Date Filter
        f_layout.addWidget(QLabel("Date Range:"))
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setStyleSheet("background-color: #0f172a; color: white; border: 1px solid #475569; padding: 5px; border-radius: 4px;")
        f_layout.addWidget(self.date_from)
        
        f_layout.addWidget(QLabel("to"))
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setStyleSheet("background-color: #0f172a; color: white; border: 1px solid #475569; padding: 5px; border-radius: 4px;")
        f_layout.addWidget(self.date_to)
        
        # Status Filter (ComboBox)
        f_layout.addWidget(QLabel("|  Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["All Values", "Paid", "Pending", "Failed"])
        self.status_combo.setFixedWidth(130)
        self.status_combo.setStyleSheet(COMBOBOX_STYLE)
        f_layout.addWidget(self.status_combo)
        
        f_layout.addStretch()
        
        # Actions
        apply_btn = QPushButton("Apply Filter")
        apply_btn.clicked.connect(self._apply_filter)
        apply_btn.setStyleSheet("background-color: #3b82f6; color: white; border-radius: 4px; padding: 6px 15px; font-weight: bold;")
        f_layout.addWidget(apply_btn)
        
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self._reset_filters)
        reset_btn.setStyleSheet("background-color: #475569; color: white; border-radius: 4px; padding: 6px 15px;")
        f_layout.addWidget(reset_btn)
        
        layout.addWidget(self.filter_frame)

        # --- Stats Bar ---
        self._create_stats_bar(layout)
        
        # --- Table ---
        self.table = QTableWidget()
        cols = ["Date", "Invoice #", "Customer", "Plan", "Amount", "Method", "Status"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self.table)
        
    def _create_stats_bar(self, layout):
        container = QHBoxLayout()
        container.setSpacing(15)
        
        def _card(key, title, icon, color_hex):
            frame = QFrame()
            frame.setStyleSheet(f"background-color: #1e293b; border-left: 4px solid {color_hex}; border-radius: 6px;")
            frame.setFixedHeight(80)
            
            l = QHBoxLayout(frame)
            l.setContentsMargins(15, 10, 15, 10)
            
            v = QVBoxLayout()
            t = QLabel(title)
            t.setStyleSheet("color: #94a3b8; font-weight: bold; font-size: 11px; background: transparent; border: none;")
            val = QLabel("0")
            val.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background: transparent; border: none;")
            self.stats_labels[key] = val
            v.addWidget(t)
            v.addWidget(val)
            l.addLayout(v)
            l.addStretch()
            
            ic = QLabel(icon)
            ic.setStyleSheet("font-size: 28px; background: transparent; border: none;")
            l.addWidget(ic)
            return frame
            
        container.addWidget(_card("TOTAL", "TOTAL INVOICES", "📄", "#3b82f6")) # Blue
        container.addWidget(_card("REV_MMK", "REVENUE (MMK)", "🇲🇲", "#8b5cf6")) # Purple
        container.addWidget(_card("REV_USD", "REVENUE (USD)", "💵", "#f59e0b")) # Orange
        
        layout.addLayout(container)

    def _toggle_filter_panel(self, checked):
        self.filter_frame.setVisible(checked)
        
    def refresh_data(self):
        self.invoices = self.manager.get_invoices()
        self._apply_filter() 
        
    def _reset_filters(self):
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        self.status_combo.setCurrentIndex(0) # All
        self.search_input.clear()
        self._apply_filter()

    def _apply_filter(self):
        # 1. Date Range
        start = self.date_from.date().toPython()
        end = self.date_to.date().toPython()
        
        # 2. Status Filter
        status_filter = self.status_combo.currentText().lower()
        if status_filter == "all values": status_filter = None
        
        # 3. Search Filter
        search_text = self.search_input.text().lower().strip()
        
        self.filtered_invoices = []
        for inv in self.invoices:
            # Date Check
            created = inv.get('created_at')
            d = None
            if hasattr(created, 'date'): d = created.date()
            elif isinstance(created, str):
                try: d = datetime.fromisoformat(created).date()
                except: pass
            
            # Check Date
            date_match = False
            if d and start <= d <= end: date_match = True
            elif not d: date_match = False 
            
            # Check Status
            status_match = True
            if status_filter:
                inv_status = str(inv.get('payment_status', 'paid')).lower()
                if status_filter not in inv_status:
                     status_match = False
                     
            # Check Search
            search_match = True
            if search_text:
                blob = (f"{inv.get('invoice_number','')} {inv.get('user_email','')} "
                        f"{inv.get('amount','')} {inv.get('license_type','')}").lower()
                if search_text not in blob:
                    search_match = False
            
            if date_match and status_match and search_match:
                self.filtered_invoices.append(inv)
                
        self._populate_table()
        self._update_stats()

    def _update_stats(self):
        count = len(self.filtered_invoices)
        mmk = 0
        usd = 0.0
        
        for inv in self.filtered_invoices:
            amt_str = str(inv.get('amount', '0'))
            try:
                if 'MMK' in amt_str:
                    mmk += int(float(amt_str.replace('MMK','').replace(',','').strip()))
                elif 'USD' in amt_str or '$' in amt_str:
                    usd += float(amt_str.replace('USD','').replace('$','').strip())
            except: pass
            
        if "TOTAL" in self.stats_labels: self.stats_labels["TOTAL"].setText(str(count))
        if "REV_MMK" in self.stats_labels: self.stats_labels["REV_MMK"].setText(f"{mmk:,} Ks")
        if "REV_USD" in self.stats_labels: self.stats_labels["REV_USD"].setText(f"${usd:,.2f}")

    def _populate_table(self):
        self.table.setRowCount(0)
        self.table.setRowCount(len(self.filtered_invoices))
        
        for r, inv in enumerate(self.filtered_invoices):
            # Date
            created = inv.get('created_at', '')
            ts_str = ""
            if hasattr(created, 'strftime'): ts_str = created.strftime("%Y-%m-%d")
            else: ts_str = str(created)[:10]
            
            self.table.setItem(r, 0, QTableWidgetItem(ts_str))
            self.table.setItem(r, 1, QTableWidgetItem(str(inv.get('invoice_number', 'N/A'))))
            self.table.setItem(r, 2, QTableWidgetItem(str(inv.get('user_email', 'Unknown'))))
            
            # Plan
            item_plan = QTableWidgetItem(str(inv.get('license_type', '-')))
            item_plan.setForeground(QColor("#cbd5e1"))
            self.table.setItem(r, 3, item_plan)
            
            # Amount
            amt = str(inv.get('amount', '0'))
            item_amt = QTableWidgetItem(amt)
            item_amt.setFont(self.table.font()) 
            if "$" in amt or "USD" in amt: item_amt.setForeground(QColor("#fbbf24")) # gold
            else: item_amt.setForeground(QColor("#a78bfa")) # purple
            self.table.setItem(r, 4, item_amt)
            
            # Method
            self.table.setItem(r, 5, QTableWidgetItem(str(inv.get('payment_method', '-'))))
            
            # Status
            st = str(inv.get('payment_status', 'Paid'))
            item_st = QTableWidgetItem(st.upper())
            if st.lower() == 'paid': item_st.setForeground(QColor("#10b981"))
            else: item_st.setForeground(QColor("#f43f5e"))
            self.table.setItem(r, 6, item_st)
            
    def _show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item: return
        
        row = item.row()
        inv = self.filtered_invoices[row]
        
        menu = QMenu(self)
        action = menu.addAction("💾 Save PDF Invoice")
        action.triggered.connect(lambda: self._save_pdf(inv))
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Invoices", "invoices.csv", "CSV (*.csv)")
        if not path: return
        try:
            import csv
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Invoice #", "Customer", "Plan", "Amount", "Method", "Status"])
                for inv in self.filtered_invoices:
                    writer.writerow([
                        inv.get('created_at', ''),
                        inv.get('invoice_number', ''),
                        inv.get('user_email', ''),
                        inv.get('license_type', ''),
                        inv.get('amount', ''),
                        inv.get('payment_method', ''),
                        inv.get('payment_status', '')
                    ])
            QMessageBox.information(self, "Success", f"Exported to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        
    def _save_pdf(self, inv_data):
        """Generate PDF Invoice using WeasyPrint"""
        from core.license_invoice_generator import LicenseInvoiceGenerator
        
        filename = f"Invoice_{inv_data.get('invoice_number', 'Copy')}.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Save Invoice", filename, "PDF Files (*.pdf)")
        if not path: return
        
        # Prepare data for generator
        # The invoice data from Firestore might use snake_case keys which is good
        # But we ensure they match what the Generator expects
        data = inv_data.copy()
        
        # Ensure fallback for display
        if 'customer_name' not in data:
            data['customer_name'] = data.get('user_email', 'Valued Customer').split('@')[0]
        
        # Generator expects 'generated_at' or we default to now
        if 'generated_at' not in data and 'created_at' in data:
            data['generated_at'] = str(data['created_at'])
            
        # -- ENRICHMENT START --
        # Fetch full user details to get Phone, HWID, etc. which might not be in invoice
        user_email = data.get('user_email')
        if user_email:
            user_doc = self.manager.get_user(user_email)
            if user_doc:
                # Force update from profile (Source of Truth) to fix issues like "treavor08" vs "treavor"
                # using the live data from the 'users' collection.
                data['customer_name'] = user_doc.get('name', data.get('customer_name', 'N/A'))
                data['phone'] = user_doc.get('phone', data.get('phone', 'N/A'))
                data['hwid'] = user_doc.get('hwid', data.get('hwid', 'N/A'))
                data['email'] = user_doc.get('email', user_email)
                
                # Also ensure address/location if we ever add it
                # data['city'] = user_doc.get('city', '')

        # Calculate Renewal Reminder
        if 'renewal_reminder' not in data:
            expiry_str = data.get('expiration_date', data.get('expiry_date'))
            if expiry_str and expiry_str != 'N/A':
                try:
                    from datetime import timedelta
                    # Try parsing (could be diverse formats)
                    # If it's a date object
                    if hasattr(expiry_str, 'strftime'):
                        d = expiry_str
                    else:
                        d = datetime.strptime(str(expiry_str)[:10], "%Y-%m-%d")
                    
                    data['renewal_reminder'] = (d - timedelta(days=30)).strftime("%Y-%m-%d")
                except:
                    data['renewal_reminder'] = "N/A"
        # -- ENRICHMENT END --
            
        try:
             generator = LicenseInvoiceGenerator()
             generator.generate_pdf(data, path)
             QMessageBox.information(self, "Success", f"Invoice saved to {path}")
        except Exception as e:
             QMessageBox.critical(self, "Error", f"Failed to save PDF: {str(e)}")
