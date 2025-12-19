# src/app/utils/validation/message_handler.py
from PySide6.QtWidgets import QMessageBox, QWidget
from PySide6.QtCore import QObject

class MessageHandler(QObject):
    """Centralized message display handler for UI messages"""

    @staticmethod
    def show_info(parent: QWidget, title: str, message: str):
        """Show info message dialog"""
        QMessageBox.information(parent, title, message)

    @staticmethod
    def show_question(parent: QWidget, title: str, message: str) -> bool:
        """Show yes/no question dialog and return True for Yes, False for No"""
        return (
            QMessageBox.question(
                parent,
                title,
                message,
                QMessageBox.Yes | QMessageBox.No
            ) == QMessageBox.Yes
        )
    
    @staticmethod
    def show_error(parent: QWidget, title: str, message: str):
        """Show error message dialog"""
        QMessageBox.critical(parent, title, message)
    
    @staticmethod
    def show_success(parent: QWidget, title: str, message: str):
        """Show success message dialog"""
        QMessageBox.information(parent, title, message)
    
    @staticmethod
    def show_warning(parent: QWidget, title: str, message: str):
        """Show warning message dialog"""
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def show_critical(parent: QWidget, title: str, message: str):
        """Show warning message dialog"""
        QMessageBox.critical(parent, title, message)