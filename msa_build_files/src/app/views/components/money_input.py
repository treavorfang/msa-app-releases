from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Qt, Signal
import re

class MoneyInput(QLineEdit):
    """
    A QLineEdit specialized for monetary input with live comma formatting.
    Displays values like "1,000".
    Formats as you type.
    """
    
    valueChanged = Signal(float)

    def __init__(self, parent=None, default_value=0.0):
        super().__init__(parent)
        self.setAlignment(Qt.AlignRight)
        
        # Initial setup
        self.setValue(default_value)
        
        self.textEdited.connect(self._on_text_edited)
        self.editingFinished.connect(self._on_editing_finished)
        
        self.setPlaceholderText("0.00")

    def value(self) -> float:
        """Returns the float value of the current text."""
        try:
            # Remove commas and any other non-numeric chars except dot and minus
            text = self.text()
            clean_text = re.sub(r'[^\d.-]', '', text)
            if not clean_text:
                return 0.0
            # Handle edge cases like "-" or "."
            if clean_text in ['-', '.', '-.']:
                return 0.0
            return float(clean_text)
        except ValueError:
            return 0.0

    def setValue(self, val: float):
        """Sets the value and updates the display text."""
        try:
            val = float(val)
        except (ValueError, TypeError):
            val = 0.0
        self.setText(f"{val:,.2f}")

    def _on_text_edited(self, text):
        """Format text with commas as user types, preserving cursor position."""
        cursor_pos = self.cursorPosition()
        
        # Count significant characters (digits, minus, dot) before the cursor
        significant_chars_before = len(re.sub(r'[^\d.-]', '', text[:cursor_pos]))
        
        # Clean the text to get raw value
        clean_text = re.sub(r'[^\d.-]', '', text)
        
        if not clean_text:
            self.valueChanged.emit(0.0)
            return

        # Prepare formatted text
        try:
            new_text = ""
            
            # Handle negative sign
            is_negative = clean_text.startswith('-')
            if is_negative:
                clean_text = clean_text[1:]
            
            # Handle decimal part
            if '.' in clean_text:
                whole, decimal = clean_text.split('.', 1)
                # Ensure whole part is formatted
                if whole:
                    formatted_whole = f"{int(whole):,}"
                else:
                    formatted_whole = "0" # Or empty string if typing ".5" -> "0.5"
                    # But if user types ".", clean_text is ".", whole="", decimal=""
                    if text.startswith('.'): formatted_whole = "0"
                
                new_text = f"{formatted_whole}.{decimal}"
            else:
                # Integer part only
                if clean_text:
                    new_text = f"{int(clean_text):,}"
                else:
                    new_text = ""
            
            if is_negative:
                new_text = "-" + new_text
                
            # If the original input was just garbage that got cleaned to empty, revert?
            # No, assume strict filtering.

            # Optimization: If text hasn't changed (e.g. typing digits), don't mess with cursor unless formatting kicked in
            # But "1000" -> "1,000" changes text.
            
            if new_text != text:
                self.blockSignals(True) # Prevent recursive calls
                self.setText(new_text)
                self.blockSignals(False)
                
                # Restore cursor position
                # Scan new_text and find position after 'significant_chars_before' significant chars
                new_cursor = 0
                count = 0
                for char in new_text:
                    new_cursor += 1
                    if char in "0123456789.-":
                        count += 1
                    if count == significant_chars_before:
                        break
                
                # Correction for trailing formatting chars logic
                # If we just typed a digit and it caused a comma to appear BEFORE it, count handles it?
                # User types '1000', cursor after last 0. Sig chars = 4.
                # New text '1,000'. 
                # '1' (1), ',' (skip), '0' (2), '0' (3), '0' (4).
                # Cursor after last 0. Correct.
                
                self.setCursorPosition(new_cursor)
        
        except ValueError:
            pass
            
        self.valueChanged.emit(self.value())

    def _on_editing_finished(self):
        """Format strictly on blur."""
        val = self.value()
        self.setText(f"{val:,.2f}")
