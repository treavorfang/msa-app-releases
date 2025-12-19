from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from typing import List, Dict
from dtos.ticket_dto import TicketDTO
from views.tickets.ticket_base import TicketBaseWidget
from utils.language_manager import language_manager

class KanbanView(TicketBaseWidget):
    """
    Kanban board view for tickets
    """
    ticket_clicked = Signal(object, TicketDTO)  # card_widget, ticket_dto
    ticket_double_clicked = Signal(TicketDTO)
    context_menu_requested = Signal(object, TicketDTO)  # global_pos, ticket_dto
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.kanban_columns = {}
        self.lm = language_manager  # Initialize language manager
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the Kanban UI"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        self.kanban_layout = QHBoxLayout(container)
        self.kanban_layout.setSpacing(12)
        self.kanban_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create columns for each status
        statuses = [
            ('open', self.lm.get('Common.open', 'Open')),
            ('diagnosed', self.lm.get('Common.diagnosed', 'Diagnosed')),
            ('in_progress', self.lm.get('Common.in_progress', 'In Progress')),
            ('awaiting_parts', self.lm.get('Common.awaiting_parts', 'Awaiting Parts')),
            ('completed', self.lm.get('Common.completed', 'Completed'))
        ]
        
        for status_key, status_label in statuses:
            column = self._create_kanban_column(status_key, status_label)
            self.kanban_columns[status_key] = column
            self.kanban_layout.addWidget(column)
        
        scroll.setWidget(container)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        
    def _create_kanban_column(self, status_key, status_label):
        """Create a single Kanban column"""
        column = QFrame()
        column.setObjectName("kanbanColumn")
        column.setMinimumWidth(180)
        column.setMaximumWidth(250)
        
        layout = QVBoxLayout(column)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Header
        header = QHBoxLayout()
        title = QLabel(status_label)
        title.setStyleSheet(f"""
            font-size: 13px;
            font-weight: bold;
            color: {self.get_status_color(status_key)};
        """)
        header.addWidget(title)
        
        count_label = QLabel("0")
        count_label.setObjectName(f"kanban_count_{status_key}")
        count_label.setStyleSheet("""
            background-color: #374151;
            color: white;
            padding: 2px 6px;
            border-radius: 8px;
            font-size: 11px;
            font-weight: bold;
        """)
        header.addWidget(count_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Cards container
        cards_scroll = QScrollArea()
        cards_scroll.setWidgetResizable(True)
        cards_scroll.setFrameShape(QFrame.NoFrame)
        cards_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        cards_container = QWidget()
        cards_container.setObjectName(f"kanban_cards_{status_key}")
        cards_layout = QVBoxLayout(cards_container)
        cards_layout.setSpacing(8)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.addStretch()
        
        cards_scroll.setWidget(cards_container)
        layout.addWidget(cards_scroll)
        
        return column
    
    def populate(self, tickets: List[TicketDTO], selected_ticket_ids: List[int] = None):
        """Populate Kanban board view"""
        if selected_ticket_ids is None:
            selected_ticket_ids = []
            
        # Group tickets by status
        tickets_by_status = {}
        for ticket in tickets:
            status = ticket.status
            if status not in tickets_by_status:
                tickets_by_status[status] = []
            tickets_by_status[status].append(ticket)
        
        # Update each column
        for status_key, column in self.kanban_columns.items():
            # Get cards container
            cards_container = column.findChild(QWidget, f"kanban_cards_{status_key}")
            if not cards_container:
                continue
            
            # Clear existing cards
            layout = cards_container.layout()
            while layout.count() > 1:  # Keep the stretch
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Add tickets for this status
            status_tickets = tickets_by_status.get(status_key, [])
            for ticket in status_tickets:
                is_selected = ticket.id in selected_ticket_ids
                card = self._create_kanban_card(ticket, is_selected)
                layout.insertWidget(layout.count() - 1, card)
            
            # Update count
            count_label = column.findChild(QLabel, f"kanban_count_{status_key}")
            if count_label:
                count_label.setText(str(len(status_tickets)))
                
    def _create_kanban_card(self, ticket: TicketDTO, is_selected: bool):
        """Create a Kanban card"""
        card = QFrame()
        card.setObjectName("kanbanCard")
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.ticket_id = ticket.id
        
        # Store ticket for click handling
        card.ticket_dto = ticket
        
        # Custom click handling for kanban cards
        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                self.ticket_clicked.emit(card, ticket)
                event.accept()
            elif event.button() == Qt.RightButton:
                try:
                    global_pos = event.globalPosition().toPoint()
                except AttributeError:
                    global_pos = event.globalPos()
                
                self.context_menu_requested.emit(global_pos, ticket)
                event.accept()
            else:
                QFrame.mousePressEvent(card, event)
            
        def mouseDoubleClickEvent(event):
            if event.button() == Qt.LeftButton:
                self.ticket_double_clicked.emit(ticket)
                
        card.mousePressEvent = mousePressEvent
        card.mouseDoubleClickEvent = mouseDoubleClickEvent
        
        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Ticket number
        ticket_num = QLabel(ticket.ticket_number)
        ticket_num.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(ticket_num)
        
        # Customer
        customer = QLabel(ticket.customer.name if ticket.customer else self.lm.get("Tickets.no_customer", "No Customer"))
        customer.setStyleSheet("font-size: 11px; color: #9CA3AF;")
        layout.addWidget(customer)
        
        # Issue (truncated)
        issue = ticket.error[:40] + "..." if ticket.error and len(ticket.error) > 40 else (ticket.error or "")
        issue_label = QLabel(issue)
        issue_label.setStyleSheet("font-size: 10px; color: #6B7280;")
        issue_label.setWordWrap(True)
        layout.addWidget(issue_label)
        
        # Technician
        tech_name = ticket.technician_name or self.lm.get("Tickets.not_assigned", "Unassigned")
        tech = QLabel(f"👤 {tech_name}")
        tech.setStyleSheet("font-size: 10px; color: #9CA3AF;")
        layout.addWidget(tech)
        
        self.update_card_style(card, is_selected)
        
        return card
        
    def update_card_style(self, card, is_selected):
        """Update card style based on selection"""
        if is_selected:
            card.setStyleSheet("""
                QFrame#kanbanCard {
                    background-color: #374151;
                    border: 2px solid #3B82F6;
                    border-radius: 6px;
                }
            """)
        else:
            card.setStyleSheet("""
                QFrame#kanbanCard {
                    background-color: #374151;
                    border: 1px solid #4B5563;
                    border-radius: 6px;
                }
                QFrame#kanbanCard:hover {
                    border-color: #3B82F6;
                    background-color: #4B5563;
                }
            """)