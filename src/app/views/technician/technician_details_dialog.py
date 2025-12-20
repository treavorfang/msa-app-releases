from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QPushButton, QLabel, QGroupBox, QTabWidget, 
                              QWidget, QTableWidget, QTableWidgetItem, QHeaderView,
                              QTextEdit, QMessageBox)
from PySide6.QtCore import Qt
from config.constants import UIColors
from datetime import datetime
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter

class TechnicianDetailsDialog(QDialog):
    """Dialog for viewing detailed technician information"""
    
    def __init__(self, container, technician, parent=None):
        super().__init__(parent)
        self.container = container
        self.technician = technician
        self.lm = language_manager
        self._setup_ui()
        
    def _setup_ui(self):
        self.setWindowTitle(f"{self.lm.get('Users.details_title', 'Technician Details')} - {self.technician.full_name}")
        self.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(self)
        
        # Header with technician name
        header_layout = QHBoxLayout()
        
        title = QLabel(f"🔧 {self.technician.full_name}")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        
        # Status badge (Active/Inactive)
        status_text = self.lm.get("Users.status_active", "Active") if self.technician.is_active else self.lm.get("Users.status_inactive", "Inactive")
        status_color = UIColors.ACTIVE if self.technician.is_active else UIColors.INACTIVE
        status_badge = QLabel(f" {status_text} ")
        status_badge.setStyleSheet(f"""
            background-color: {status_color}; 
            color: white; 
            border-radius: 4px; 
            padding: 4px; 
            font-weight: bold;
        """)
        header_layout.addWidget(status_badge)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Tab widget for different sections
        tabs = QTabWidget()
        
        # Contact Info Tab
        tabs.addTab(self._create_contact_tab(), self.lm.get("Common.contact_info", "Contact Info"))
        
        # Assigned Tickets Tab
        tabs.addTab(self._create_tickets_tab(), self.lm.get("Tickets.assigned_tickets", "Assigned Tickets"))
        
        # Performance Tab
        tabs.addTab(self._create_performance_tab(), self.lm.get("Users.performance_dashboard", "Performance"))
        
        # Work Logs Tab
        tabs.addTab(self._create_work_logs_tab(), self.lm.get("Common.work_logs", "Work Logs"))
        
        layout.addWidget(tabs)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        edit_btn = QPushButton(self.lm.get("Users.edit_title", "Edit Technician"))
        edit_btn.clicked.connect(self._on_edit)
        button_layout.addWidget(edit_btn)
        
        bonus_btn = QPushButton(f"💰 {self.lm.get('Users.manage_bonuses', 'Manage Bonuses')}")
        bonus_btn.clicked.connect(self._show_bonus_dialog)
        button_layout.addWidget(bonus_btn)
        
        performance_btn = QPushButton(f"📊 {self.lm.get('Users.performance_dashboard', 'Performance Dashboard')}")
        performance_btn.clicked.connect(self._show_performance_dialog)
        button_layout.addWidget(performance_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton(self.lm.get("Common.close", "Close"))
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_contact_tab(self):
        """Create contact information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Contact Details Group
        contact_group = QGroupBox(self.lm.get("Common.contact_details", "Contact Details"))
        contact_layout = QFormLayout(contact_group)
        
        contact_layout.addRow(f"{self.lm.get('Common.full_name', 'Full Name')}:", QLabel(self.technician.full_name or "N/A"))
        contact_layout.addRow(f"{self.lm.get('Common.email', 'Email')}:", QLabel(self.technician.email or "N/A"))
        contact_layout.addRow(f"{self.lm.get('Common.phone', 'Phone')}:", QLabel(self.technician.phone or "N/A"))
        
        layout.addWidget(contact_group)
        
        # Qualifications Group
        qual_group = QGroupBox(self.lm.get("Technicians.qualifications", "Qualifications"))
        qual_layout = QFormLayout(qual_group)
        
        qual_layout.addRow(f"{self.lm.get('Technicians.certification', 'Certification')}:", QLabel(self.technician.certification or "N/A"))
        qual_layout.addRow(f"{self.lm.get('Technicians.specialization', 'Specialization')}:", QLabel(self.technician.specialization or "N/A"))
        
        layout.addWidget(qual_group)
        
        # Timeline Group
        time_group = QGroupBox(self.lm.get("Common.timeline", "Timeline"))
        time_layout = QFormLayout(time_group)
        
        created_at = self.technician.joined_at.strftime("%Y-%m-%d %H:%M") if self.technician.joined_at else "N/A"
        time_layout.addRow(f"{self.lm.get('Technicians.joined_header', 'Joined')}:", QLabel(created_at))
        
        layout.addWidget(time_group)
        layout.addStretch()
        
        return widget
    
    def _create_tickets_tab(self):
        """Create assigned tickets tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Get tickets assigned to this technician via Service
        tickets = self.container.ticket_service.get_tickets_by_technician(self.technician.id, limit=50)
        
        if not tickets:
            no_tickets_label = QLabel(self.lm.get("Tickets.no_tickets_assigned", "No tickets assigned yet."))
            no_tickets_label.setAlignment(Qt.AlignCenter)
            no_tickets_label.setStyleSheet("color: gray; font-style: italic;")
            layout.addWidget(no_tickets_label)
        else:
            # Tickets table
            tickets_table = QTableWidget()
            tickets_table.setColumnCount(5)
            tickets_table.setHorizontalHeaderLabels([
                self.lm.get("Tickets.ticket_number_header", "Ticket #"),
                self.lm.get("Common.customer_header", "Customer"),
                self.lm.get("Common.device_header", "Device"),
                self.lm.get("Common.status_header", "Status"),
                self.lm.get("Common.created_header", "Created")
            ])
            tickets_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            tickets_table.setSelectionBehavior(QTableWidget.SelectRows)
            tickets_table.setEditTriggers(QTableWidget.NoEditTriggers)
            
            tickets_table.setRowCount(len(tickets))
            
            for row, ticket in enumerate(tickets):
                tickets_table.setItem(row, 0, QTableWidgetItem(ticket.ticket_number))
                
                # Handle DTO nesting
                customer_name = "N/A"
                if ticket.customer:
                    customer_name = ticket.customer.name
                
                tickets_table.setItem(row, 1, QTableWidgetItem(customer_name))
                
                device_info = "N/A"
                if ticket.device:
                    brand = getattr(ticket.device, 'brand', '')
                    model = getattr(ticket.device, 'model', '')
                    device_info = f"{brand} {model}".strip()
                
                tickets_table.setItem(row, 2, QTableWidgetItem(device_info))
                
                status_item = QTableWidgetItem(ticket.status.upper())
                if ticket.status == 'completed':
                    status_item.setForeground(Qt.green)
                elif ticket.status in ['in_progress', 'diagnosed']:
                    status_item.setForeground(Qt.blue)
                tickets_table.setItem(row, 3, status_item)
                
                created = ticket.created_at.strftime("%Y-%m-%d") if ticket.created_at else "N/A"
                tickets_table.setItem(row, 4, QTableWidgetItem(created))
            
            layout.addWidget(tickets_table)
            
            # Summary
            summary_label = QLabel(f"{self.lm.get('Tickets.total_assigned_tickets', 'Total Assigned Tickets')}: {len(tickets)}")
            summary_label.setStyleSheet("font-weight: bold; padding: 5px;")
            layout.addWidget(summary_label)
        
        return widget
    
    def _create_performance_tab(self):
        """Create performance statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Get performance stats via Service (fetching all tickets for calc)
        all_tickets = self.container.ticket_service.get_tickets_by_technician(self.technician.id, limit=500)
        
        total_tickets = len(all_tickets)
        completed_tickets = len([t for t in all_tickets if t.status == 'completed'])
        in_progress = len([t for t in all_tickets if t.status in ['in_progress', 'diagnosed']])
        
        completion_rate = (completed_tickets / total_tickets * 100) if total_tickets > 0 else 0
        
        # Stats Group
        stats_group = QGroupBox(self.lm.get("Users.performance_statistics", "Performance Statistics"))
        stats_layout = QFormLayout(stats_group)
        
        stats_layout.addRow(f"{self.lm.get('Users.total_assigned', 'Total Assigned')}:", QLabel(str(total_tickets)))
        stats_layout.addRow(f"{self.lm.get('Common.completed', 'Completed')}:", QLabel(f"{completed_tickets} ({completion_rate:.1f}%)"))
        stats_layout.addRow(f"{self.lm.get('Common.in_progress', 'In Progress')}:", QLabel(str(in_progress)))
        
        # Calculate total revenue
        total_revenue = sum(float(t.actual_cost) for t in all_tickets if t.status == 'completed')
        stats_layout.addRow(f"{self.lm.get('Users.total_revenue', 'Total Revenue')}:", QLabel(currency_formatter.format(total_revenue)))
        
        layout.addWidget(stats_group)
        
        # Status breakdown
        status_group = QGroupBox(self.lm.get("Users.status_breakdown", "Status Breakdown"))
        status_layout = QFormLayout(status_group)
        
        status_counts = {}
        for ticket in all_tickets:
            status_counts[ticket.status] = status_counts.get(ticket.status, 0) + 1
        
        for status, count in sorted(status_counts.items()):
            status_layout.addRow(f"{status.title()}:", QLabel(str(count)))
        
        layout.addWidget(status_group)
        layout.addStretch()
        
        return widget
    
    def _create_work_logs_tab(self):
        """Create work logs tab showing all work performed by this technician"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Get all work logs for this technician via Service
        work_logs = self.container.work_log_service.get_logs_for_technician(self.technician.id, limit=100)
        
        if not work_logs:
            no_logs_label = QLabel(self.lm.get("Common.no_work_logs", "No work logs recorded yet."))
            no_logs_label.setAlignment(Qt.AlignCenter)
            no_logs_label.setStyleSheet("color: gray; font-style: italic;")
            layout.addWidget(no_logs_label)
        else:
            # Summary stats
            summary_group = QGroupBox(self.lm.get("Common.work_summary", "Work Summary"))
            summary_layout = QFormLayout(summary_group)
            
            total_logs = len(work_logs)
            completed_logs = len([log for log in work_logs if log.end_time])
            active_logs = total_logs - completed_logs
            
            # Calculate total time
            total_minutes = 0
            for log in work_logs:
                if log.end_time:
                    duration = (log.end_time - log.start_time).total_seconds() / 60
                    total_minutes += duration
            
            total_hours = total_minutes / 60
            
            summary_layout.addRow(f"{self.lm.get('Common.total_work_sessions', 'Total Work Sessions')}:", QLabel(str(total_logs)))
            summary_layout.addRow(f"{self.lm.get('Common.completed_sessions', 'Completed Sessions')}:", QLabel(str(completed_logs)))
            summary_layout.addRow(f"{self.lm.get('Common.active_sessions', 'Active Sessions')}:", QLabel(str(active_logs)))
            summary_layout.addRow(f"{self.lm.get('Common.total_time_logged', 'Total Time Logged')}:", QLabel(f"{total_hours:.1f} {self.lm.get('Common.hours', 'hours')} ({total_minutes:.0f} {self.lm.get('Common.minutes', 'minutes')})"))
            
            layout.addWidget(summary_group)
            
            # Work logs table
            logs_table = QTableWidget()
            logs_table.setColumnCount(6)
            logs_table.setHorizontalHeaderLabels([
                self.lm.get("Tickets.ticket_number_header", "Ticket #"),
                self.lm.get("Common.work_performed", "Work Performed"),
                self.lm.get("Common.start_time", "Start Time"),
                self.lm.get("Common.end_time", "End Time"),
                self.lm.get("Common.duration", "Duration"),
                self.lm.get("Common.status_header", "Status")
            ])
            logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            logs_table.setSelectionBehavior(QTableWidget.SelectRows)
            logs_table.setEditTriggers(QTableWidget.NoEditTriggers)
            logs_table.setAlternatingRowColors(True)
            
            logs_table.setRowCount(len(work_logs))
            
            for row, log in enumerate(work_logs):
                # Ticket number (Handle DTO optionality)
                ticket_num = log.ticket_number if hasattr(log, 'ticket_number') and log.ticket_number else "N/A"
                # Fallback if DTO structure is different (e.g. log.ticket is object)
                if ticket_num == "N/A" and hasattr(log, 'ticket') and log.ticket:
                     ticket_num = getattr(log.ticket, 'ticket_number', 'N/A')
                     
                logs_table.setItem(row, 0, QTableWidgetItem(ticket_num))
                
                # Work performed (truncate if too long)
                work_text = log.work_performed[:50] + "..." if len(log.work_performed) > 50 else log.work_performed
                logs_table.setItem(row, 1, QTableWidgetItem(work_text))
                
                # Start time
                start_time = log.start_time.strftime("%Y-%m-%d %H:%M") if log.start_time else "N/A"
                logs_table.setItem(row, 2, QTableWidgetItem(start_time))
                
                # End time
                end_time = log.end_time.strftime("%Y-%m-%d %H:%M") if log.end_time else "In Progress"
                end_item = QTableWidgetItem(end_time)
                if not log.end_time:
                    end_item.setForeground(Qt.blue)
                logs_table.setItem(row, 3, end_item)
                
                # Duration
                if log.end_time:
                    duration_seconds = (log.end_time - log.start_time).total_seconds()
                    duration_minutes = duration_seconds / 60
                    if duration_minutes < 60:
                        duration_str = f"{duration_minutes:.0f} min"
                    else:
                        hours = duration_minutes / 60
                        duration_str = f"{hours:.1f} hrs"
                    logs_table.setItem(row, 4, QTableWidgetItem(duration_str))
                else:
                    logs_table.setItem(row, 4, QTableWidgetItem("-"))
                
                # Status
                status = "Active" if not log.end_time else "Completed"
                status_item = QTableWidgetItem(status)
                if status == "Active":
                    status_item.setForeground(Qt.blue)
                else:
                    status_item.setForeground(Qt.green)
                logs_table.setItem(row, 5, status_item)
            
            layout.addWidget(logs_table)
        
        return widget
    
    def _on_edit(self):
        """Open edit dialog"""
        # We need to access the parent's edit method
        if hasattr(self.parent(), 'show_add_technician_dialog'):
            self.accept()  # Close details dialog
            self.parent().show_add_technician_dialog(self.technician)
    
    def _show_bonus_dialog(self):
        """Show bonus management dialog"""
        from views.technician.bonus_management_dialog import BonusManagementDialog
        dialog = BonusManagementDialog(self.container, self.technician, self)
        dialog.exec()
    
    def _show_performance_dialog(self):
        """Show performance dashboard dialog"""
        from views.technician.performance_dashboard_dialog import PerformanceDashboardDialog
        dialog = PerformanceDashboardDialog(self.container, self.technician, self)
        dialog.exec()
