# src/app/views/tickets/ticket_base.py
from PySide6.QtWidgets import QWidget, QDialog
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter

class TicketBase:
    """Base class for all ticket-related views providing common functionality"""
    
    def __init__(self, *args, **kwargs):
        # These will be set by the actual widget's __init__
        self.lm = language_manager
        self.cf = currency_formatter
    
    def tr(self, text, default=None):
        """Shortcut method for translation"""
        if default is None:
            default = text
        return self.lm.get(text, default)
    
    def format_currency(self, amount, currency_code=None):
        """Format currency amount"""
        if currency_code:
            return self.cf.format(amount, currency_code)
        return self.cf.format(amount)
    
    def get_status_color(self, status):
        """Get color for status badge - can be overridden by subclasses"""
        colors = {
            'open': '#4169E1',           # Royal Blue
            'in_progress': '#DAA520',    # Goldenrod
            'awaiting_parts': '#FF8C00', # Dark Orange
            'completed': '#32CD32',      # Lime Green
            'cancelled': '#DC143C',      # Crimson
            'unrepairable': '#696969',   # Dim Gray
            'diagnosed': '#BA55D3'       # Medium Orchid
        }
        return colors.get(status, '#808080')
    
    def get_priority_color(self, priority):
        """Get color for priority badge"""
        colors = {
            'low': '#10B981',      # Green
            'medium': '#F59E0B',   # Orange
            'high': '#EF4444',     # Red
            'critical': '#DC2626'    # Dark Red
        }
        return colors.get(priority, '#6B7280')


class TicketBaseWidget(TicketBase, QWidget):
    """Base class for ticket widgets"""
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        TicketBase.__init__(self)
        self._init_base_ui()
    
    def _init_base_ui(self):
        """Initialize base UI elements if needed"""
        pass


class TicketBaseDialog(TicketBase, QDialog):
    """Base class for ticket dialogs"""
    
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        TicketBase.__init__(self)
        self._init_base_ui()
    
    def _init_base_ui(self):
        """Initialize base UI elements if needed"""
        pass