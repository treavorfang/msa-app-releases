"""
UI Styles and themes for License Generator - Unified Design System
"""

# Color Palette
COLORS = {
    'bg_main': '#0f172a',       # Dark Slate 950
    'bg_card': '#1e293b',       # Dark Slate 800
    'bg_input': '#1e293b',      # Dark Slate 800
    'border': '#334155',        # Dark Slate 700
    'border_focus': '#3b82f6',  # Blue 500
    'text_primary': '#e2e8f0',  # Slate 200
    'text_secondary': '#94a3b8',# Slate 400
    'primary': '#3b82f6',       # Blue 500
    'primary_hover': '#2563eb', # Blue 600
    'success': '#10b981',       # Emerald 500
    'danger': '#ef4444',        # Red 500
    'warning': '#f59e0b',       # Amber 500
    'purple': '#8b5cf6',        # Violet 500
}

# --- ATOMIC COMPONENT STYLES ---

# Input Fields (LineEdit, DateEdit, TextEdit)
INPUT_STYLE = """
    QLineEdit, QDateEdit, QTextEdit {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 6px;
        color: #e2e8f0;
        padding: 8px 12px;
        font-size: 14px;
        selection-background-color: #3b82f6;
        selection-color: white;
    }
    QLineEdit:focus, QDateEdit:focus, QTextEdit:focus {
        border: 1px solid #3b82f6;
        background-color: #0f172a;
    }
    QLineEdit::placeholder { color: #64748b; }
"""

# ComboBox
COMBOBOX_STYLE = """
    QComboBox {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 6px;
        color: #e2e8f0;
        padding: 8px 12px;
        font-size: 14px;
    }
    QComboBox:focus {
        border: 1px solid #3b82f6;
    }
    QComboBox::drop-down {
        border: none;
        width: 20px;
        margin-right: 5px;
    }
    QComboBox::down-arrow {
        image: none; 
        border: none;
        width: 0; 
        height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid #94a3b8;
        margin: 0;
    }
    QComboBox QAbstractItemView {
        background-color: #1e293b;
        color: #e2e8f0;
        border: 1px solid #334155;
        selection-background-color: #3b82f6;
        selection-color: white;
        outline: none;
    }
"""

# Buttons
BUTTON_PRIMARY_STYLE = """
    QPushButton {
        background-color: #3b82f6;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: bold;
    }
    QPushButton:hover { background-color: #2563eb; }
    QPushButton:pressed { background-color: #1d4ed8; }
    QPushButton:disabled { background-color: #475569; color: #94a3b8; }
"""

BUTTON_SECONDARY_STYLE = """
    QPushButton {
        background-color: #334155;
        color: #e2e8f0;
        border: 1px solid #475569;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: bold;
    }
    QPushButton:hover { background-color: #475569; border-color: #64748b; }
    QPushButton:pressed { background-color: #1e293b; }
"""

BUTTON_danger_STYLE = """
    QPushButton {
        background-color: #ef4444;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: bold;
    }
    QPushButton:hover { background-color: #dc2626; }
"""

BUTTON_SUCCESS_STYLE = """
    QPushButton {
        background-color: #10b981;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: bold;
    }
    QPushButton:hover { background-color: #059669; }
"""

# Tables
TABLE_STYLE = """
    QTableWidget {
        background-color: #1e293b;
        color: #e2e8f0;
        gridline-color: #334155;
        border: 1px solid #334155;
        border-radius: 8px;
        font-size: 13px;
        outline: none;
    }
    QTableWidget::item {
        padding: 10px;
        border-bottom: 1px solid #334155;
    }
    QTableWidget::item:selected {
        background-color: #3b82f6;
        color: white;
    }
    QHeaderView::section {
        background-color: #0f172a;
        color: #94a3b8;
        padding: 12px;
        border: none;
        border-bottom: 2px solid #334155;
        font-weight: bold;
        font-size: 12px;
        text-transform: uppercase;
    }
    QTableWidget::item:focus {
        border: none;
        outline: none;
    }
"""

# Scrollbars (Modern Thin)
SCROLLBAR_STYLE = """
    QScrollBar:vertical {
        border: none;
        background: #0f172a;
        width: 10px;
        margin: 0;
    }
    QScrollBar::handle:vertical {
        background: #475569;
        min-height: 20px;
        border-radius: 5px;
    }
    QScrollBar::handle:vertical:hover { background: #64748b; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""

# Group Box
GROUP_BOX_STYLE = """
    QGroupBox {
        font-size: 13px;
        font-weight: bold;
        color: #3b82f6;
        border: 1px solid #334155;
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 24px;
        background-color: #1e293b; /* Slightly lighter than main bg */
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 15px;
        top: 0px;
        padding: 0 5px;
        background-color: #1e293b; 
    }
"""

# Tab Widget
TAB_STYLE = """
    QTabWidget::pane {
        border: 1px solid #334155;
        background-color: #0f172a;
        border-radius: 8px;
    }
    QTabBar::tab {
        background-color: #1e293b;
        color: #94a3b8;
        padding: 12px 20px;
        margin-right: 4px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-weight: bold;
        font-size: 13px;
        border: 1px solid #334155;
        border-bottom: none;
    }
    QTabBar::tab:selected {
        background-color: #3b82f6;
        color: white;
        border-color: #3b82f6;
    }
    QTabBar::tab:hover:!selected {
        background-color: #334155;
        color: #cbd5e1;
    }
"""

# Context Menu
MENU_STYLE = """
    QMenu {
        background-color: #1e293b;
        color: #e2e8f0;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 5px;
    }
    QMenu::item {
        padding: 8px 25px 8px 15px;
        border-radius: 4px;
    }
    QMenu::item:selected {
        background-color: #3b82f6;
        color: white;
    }
    QMenu::separator {
        height: 1px;
        background: #334155;
        margin: 5px 0;
    }
"""

# Card Styles
CARD_STYLE_BASE = """
    QFrame {
        border-radius: 12px;
        background-color: #1e293b;
        border: 1px solid #334155;
    }
    QLabel {
        background-color: transparent;
        border: none;
    }
"""

CARD_STYLE = CARD_STYLE_BASE # Added alias for backward compatibility

CARD_BLUE = """
    QFrame {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e3a8a, stop:1 #2563eb);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    QLabel {
        background-color: transparent;
        border: none;
    }
"""
CARD_GREEN = """
    QFrame {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #064e3b, stop:1 #059669);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    QLabel {
        background-color: transparent;
        border: none;
    }
"""
CARD_PURPLE = """
    QFrame {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4c1d95, stop:1 #7c3aed);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    QLabel {
        background-color: transparent;
        border: none;
    }
"""
CARD_ORANGE = """
    QFrame {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #78350f, stop:1 #d97706);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    QLabel {
        background-color: transparent;
        border: none;
    }
"""

# --- COMPOSITE STYLES ---

# Standard Dialog (combines inputs, buttons, etc)
DIALOG_STYLE = f"""
    QDialog {{
        background-color: #0f172a;
        color: #e2e8f0;
    }}
    QLabel {{
        color: #e2e8f0;
        font-size: 14px;
    }}
    {INPUT_STYLE}
    {COMBOBOX_STYLE}
    {TABLE_STYLE}
    {SCROLLBAR_STYLE}
    {MENU_STYLE}
    QDialogButtonBox QPushButton {{ 
        /* Standardize dialog buttons */
        background-color: #3b82f6; 
        color: white; 
        border: none; 
        border-radius: 6px;
        padding: 8px 16px; 
        font-weight: bold; 
        font-size: 14px;
    }}
    QDialogButtonBox QPushButton:hover {{ background-color: #2563eb; }}
    QDialogButtonBox QPushButton[text="Cancel"] {{ 
        background-color: #334155; 
        border: 1px solid #475569; 
    }}
    QDialogButtonBox QPushButton[text="Cancel"]:hover {{ background-color: #475569; }}
"""

# Main Window (Global)
MAIN_WINDOW_STYLE = f"""
    QMainWindow, QWidget {{
        background-color: #0f172a;
        color: #e2e8f0;
    }}
    QLabel {{
        color: #e2e8f0;
    }}
    {INPUT_STYLE}
    {COMBOBOX_STYLE}
    {TABLE_STYLE}
    {SCROLLBAR_STYLE}
    {MENU_STYLE}
    {TAB_STYLE}
"""

# Specific component aliases
GENERATE_BUTTON_STYLE = BUTTON_PRIMARY_STYLE
HISTORY_BUTTON_STYLE = BUTTON_SECONDARY_STYLE
