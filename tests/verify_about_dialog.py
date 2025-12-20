
import sys
import os
from PySide6.QtWidgets import QApplication

# Adjust path to find src/app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/app')))

from views.dialogs.about_dialog import AboutDialog

def test_about_dialog():
    app = QApplication(sys.argv)
    try:
        # Try to instantiate the dialog
        dialog = AboutDialog()
        print("✅ AboutDialog instantiated successfully.")
        
        # Check if version info is present (checking if it rendered without error is implicit)
        print("✅ Imports verification passed.")
        
    except NameError as e:
        print(f"❌ NameError: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_about_dialog()
