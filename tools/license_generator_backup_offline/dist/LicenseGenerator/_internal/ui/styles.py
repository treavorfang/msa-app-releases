"""
UI Styles and themes for License Generator
"""

# Main window stylesheet
MAIN_WINDOW_STYLE = """
    QMainWindow {
        background-color: #1e293b;
        color: #e2e8f0;
    }
    QLabel {
        color: #e2e8f0;
        font-size: 14px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    QLineEdit, QDateEdit, QTextEdit {
        background-color: #334155;
        border: 1px solid #475569;
        border-radius: 6px;
        color: white;
        padding: 10px;
        font-size: 14px;
        selection-background-color: #3b82f6;
    }
    QLineEdit:focus, QDateEdit:focus, QTextEdit:focus {
        border: 1px solid #3b82f6;
    }
    QPushButton {
        background-color: #3b82f6;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 12px;
        font-size: 14px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #2563eb;
    }
    QPushButton:pressed {
        background-color: #1d4ed8;
    }
    QPushButton#copyButton {
        background-color: #10b981;
    }
    QPushButton#copyButton:hover {
        background-color: #059669;
    }
    QFrame#separator {
        border: 1px solid #475569;
        margin-top: 10px;
        margin-bottom: 10px;
    }
"""

# ComboBox stylesheet
COMBOBOX_STYLE = """
    QComboBox {
        background-color: #334155;
        border: 1px solid #475569;
        border-radius: 6px;
        color: white;
        padding: 10px;
        font-size: 14px;
    }
    QComboBox:focus {
        border: 1px solid #3b82f6;
    }
    QComboBox::drop-down {
        border: none;
    }
    QComboBox QAbstractItemView {
        background-color: #334155;
        color: white;
        selection-background-color: #3b82f6;
    }
"""

# Generate button stylesheet
GENERATE_BUTTON_STYLE = """
    QPushButton {
        background-color: #3b82f6;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 12px;
        font-size: 15px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #2563eb;
    }
    QPushButton:pressed {
        background-color: #1d4ed8;
    }
"""

# History button stylesheet
HISTORY_BUTTON_STYLE = """
    QPushButton#historyButton {
        background-color: #6366f1;
    }
    QPushButton#historyButton:hover {
        background-color: #4f46e5;
    }
"""

# Tab stylesheet
TAB_STYLE = """
    QTabWidget::pane {
        border: 1px solid #334155;
        background-color: #0f172a;
        border-radius: 8px;
    }
    QTabBar::tab {
        background-color: #1e293b;
        color: #94a3b8;
        padding: 12px 24px;
        margin-right: 4px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        font-weight: bold;
        font-size: 14px;
    }
    QTabBar::tab:selected {
        background-color: #3b82f6;
        color: white;
    }
    QTabBar::tab:hover:!selected {
        background-color: #334155;
    }
"""

# Group box stylesheet
GROUP_BOX_STYLE = """
    QGroupBox {
        font-size: 15px;
        font-weight: bold;
        color: #3b82f6;
        border: 2px solid #334155;
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 20px;
        background-color: #0f172a;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 15px;
        padding: 0 8px;
        background-color: #0f172a; 
    }
"""

# Card stylesheet - COLORFUL VARIANTS
CARD_STYLE_BASE = """
    QFrame {
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    QLabel {
        background-color: transparent;
        border: none;
    }
    QLabel#CardTitle {
        color: rgba(255, 255, 255, 0.7);
        font-size: 13px;
        font-weight: bold;
        background-color: transparent;
    }
    QLabel#CardValue {
        color: white;
        font-size: 24px;
        font-weight: bold;
        background-color: transparent;
    }
"""

# Alias for backward compatibility if needed
CARD_STYLE = CARD_STYLE_BASE

CARD_BLUE = CARD_STYLE_BASE + """
    QFrame {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e3a8a, stop:1 #3b82f6);
    }
"""

CARD_GREEN = CARD_STYLE_BASE + """
    QFrame {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #064e3b, stop:1 #10b981);
    }
"""

CARD_ORANGE = CARD_STYLE_BASE + """
    QFrame {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #78350f, stop:1 #f59e0b);
    }
"""

CARD_PURPLE = CARD_STYLE_BASE + """
    QFrame {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4c1d95, stop:1 #8b5cf6);
    }
"""

# Dialog stylesheet
DIALOG_STYLE = """
    QDialog {
        background-color: #0f172a;
        color: #e2e8f0;
    }
    QLabel {
        color: #e2e8f0;
    }
    QLineEdit {
        background-color: #1e293b;
        border: 1px solid #475569;
        border-radius: 8px;
        color: white;
        padding: 12px;
        font-size: 14px;
    }
    QLineEdit:focus {
        border: 1px solid #3b82f6;
        background-color: #334155;
    }
    QTableWidget {
        background-color: #1e293b;
        color: #e2e8f0;
        gridline-color: transparent;
        border: 1px solid #334155;
        border-radius: 8px;
        font-size: 14px;
        selection-background-color: #3b82f6;
        selection-color: white;
    }
    QTableWidget::item {
        padding: 12px;
        border-bottom: 1px solid #334155;
    }
    QTableWidget::item:hover {
        background-color: #334155;
    }
    QHeaderView::section {
        background-color: #0f172a;
        color: #94a3b8;
        padding: 12px;
        border: none;
        border-bottom: 2px solid #334155;
        font-weight: bold;
        font-size: 13px;
        text-transform: uppercase;
    }
    QMenu {
        background-color: #1e293b;
        color: #e2e8f0;
        border: 1px solid #475569;
        padding: 5px;
        border-radius: 6px;
    }
    QMenu::item {
        padding: 5px 20px;
        border-radius: 4px;
    }
    QMenu::item:selected {
        background-color: #3b82f6;
    }
"""

# Color constants
COLORS = {
    'blue': '#3b82f6',
    'green': '#10b981',
    'yellow': '#f59e0b',
    'red': '#ef4444',
    'purple': '#8b5cf6',
    'gray': '#94a3b8',
    'dark_blue': '#1e293b',
}
