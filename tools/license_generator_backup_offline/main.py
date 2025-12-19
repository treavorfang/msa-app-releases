"""
MSA License Generator - Entry Point

A standalone tool for generating and managing MSA application licenses.
"""
import sys
from PySide6.QtWidgets import QApplication

from ui import LicenseGeneratorWindow


def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("MSA License Generator")
    app.setOrganizationName("Studio Tai")
    
    # Create and show main window
    window = LicenseGeneratorWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
