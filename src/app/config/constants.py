# src/app/config/constants.py
"""
Application-wide constants for the MSA application.
Centralizes magic strings, numbers, and configuration values.
"""

class TicketStatus:
    """Ticket status constants"""
    OPEN = 'open'
    DIAGNOSED = 'diagnosed'
    IN_PROGRESS = 'in_progress'
    AWAITING_PARTS = 'awaiting_parts'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    UNREPAIRABLE = 'unrepairable'
    
    ALL = [OPEN, DIAGNOSED, IN_PROGRESS, AWAITING_PARTS, COMPLETED, CANCELLED, UNREPAIRABLE]
    
    @classmethod
    def get_display_name(cls, status: str) -> str:
        """Get human-readable status name"""
        return status.replace('_', ' ').title()


class TicketPriority:
    """Ticket priority constants"""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'
    
    ALL = [LOW, MEDIUM, HIGH, CRITICAL]


class PurchaseOrderStatus:
    """Purchase order status constants"""
    DRAFT = 'draft'
    SENT = 'sent'
    RECEIVED = 'received'
    
    ALL = [DRAFT, SENT, RECEIVED]


class InvoiceStatus:
    """Invoice status constants"""
    PENDING = 'pending'
    PARTIAL = 'partial'
    PAID = 'paid'
    OVERDUE = 'overdue'
    
    ALL = [PENDING, PARTIAL, PAID, OVERDUE]


class PaymentMethod:
    """Payment method constants"""
    BANK_TRANSFER = 'bank_transfer'
    CASH = 'cash'
    CHECK = 'check'
    CREDIT_CARD = 'credit_card'
    OTHER = 'other'
    
    ALL = [BANK_TRANSFER, CASH, CHECK, CREDIT_CARD, OTHER]
    
    DISPLAY_NAMES = {
        BANK_TRANSFER: 'Bank Transfer',
        CASH: 'Cash',
        CHECK: 'Check',
        CREDIT_CARD: 'Credit Card',
        OTHER: 'Other'
    }


class UIColors:
    """UI color constants"""
    SUCCESS = '#2ecc71'
    ERROR = '#e74c3c'
    WARNING = '#f39c12'
    INFO = '#3498db'
    ACTIVE = '#2ecc71'
    INACTIVE = '#e74c3c'
    PENDING = '#f39c12'
    COMPLETED = '#2ecc71'


class Limits:
    """Application limits and constraints"""
    TICKET_NUMBER_MAX = 9999
    TICKET_NUMBER_MIN = 1
    MAX_SEARCH_RESULTS = 100
    DEFAULT_INVOICE_DUE_DAYS = 30
    MIN_PASSWORD_LENGTH = 6


class TicketNumbering:
    """Ticket numbering configuration"""
    PREFIX = 'RPT'
    DATE_FORMAT = '%y%m%d'  # YYMMDD
    SEQUENCE_FORMAT = '{:04d}'  # 0001-9999
    FULL_FORMAT = '{prefix}-{branch_id}{date}-{sequence}'


class InvoiceNumbering:
    """Invoice numbering configuration"""
    PREFIX = 'INV'
    DATE_FORMAT = '%y%m%d'  # YYMMDD
    SEQUENCE_FORMAT = '{:04d}'  # 0001-9999
    FULL_FORMAT = '{prefix}-{branch_id}{date}-{sequence}'


class ContactMethod:
    """Preferred contact method constants"""
    PHONE = 'phone'
    EMAIL = 'email'
    SMS = 'sms'
    
    ALL = [PHONE, EMAIL, SMS]


class UserRole:
    """User role constants"""
    ADMIN = 'admin'
    TECHNICIAN = 'technician'
    STAFF = 'staff'
    
    ALL = [ADMIN, TECHNICIAN, STAFF]


class Theme:
    """Theme constants"""
    LIGHT = 'light'
    DARK = 'dark'
    
    DEFAULT = LIGHT


class PurchaseReturnStatus:
    """Purchase return status constants"""
    DRAFT = 'draft'
    APPROVED = 'approved'
    COMPLETED = 'completed'
    
    ALL = [DRAFT, APPROVED, COMPLETED]


class ReturnCondition:
    """Return item condition constants"""
    DEFECTIVE = 'defective'
    DAMAGED = 'damaged'
    UNOPENED = 'unopened'
    WRONG_ITEM = 'wrong_item'
    
    ALL = [DEFECTIVE, DAMAGED, UNOPENED, WRONG_ITEM]
    
    DISPLAY_NAMES = {
        DEFECTIVE: 'Defective',
        DAMAGED: 'Damaged',
        UNOPENED: 'Unopened',
        WRONG_ITEM: 'Wrong Item'
    }


class CreditNoteStatus:
    """Credit note status constants"""
    PENDING = 'pending'
    APPLIED = 'applied'
    EXPIRED = 'expired'
    
    ALL = [PENDING, APPLIED, EXPIRED]
