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
        self.symbol = ""
        self.symbol_position = "before" # 'before' or 'after'
        
        # Initial setup
        self.setValue(default_value)
        
        self.textEdited.connect(self._on_text_edited)
        self.editingFinished.connect(self._on_editing_finished)
        
        self.setPlaceholderText("0.00")

    def set_currency(self, symbol: str, position: str = "before"):
        """Configure currency symbol and position."""
        self.symbol = symbol
        self.symbol_position = position
        # Refresh display
        self.setValue(self.value())

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
            
        formatted = f"{val:,.2f}"
        if self.symbol:
            if self.symbol_position == "before":
                self.setText(f"{self.symbol} {formatted}")
            else:
                self.setText(f"{formatted} {self.symbol}")
        else:
            self.setText(formatted)

    def set_value(self, val: float):
        """Alias for setValue for compatibility."""
        self.setValue(val)

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
                    if text.startswith('.') or (self.symbol and self.symbol in text[:text.find('.')]): 
                        pass # complicated check? if original had . just assume 0.
                        formatted_whole = "0"
                
                new_text = f"{formatted_whole}.{decimal}"
            else:
                # Integer part only
                if clean_text:
                    new_text = f"{int(clean_text):,}"
                else:
                    new_text = ""
            
            if is_negative:
                new_text = "-" + new_text
            
            # Apply symbol
            if self.symbol:
                if self.symbol_position == "before":
                    new_text = f"{self.symbol} {new_text}"
                else:
                    new_text = f"{new_text} {self.symbol}"
                
            # If the original input was just garbage that got cleaned to empty, revert?
            # No, assume strict filtering.

            # Optimization: If text hasn't changed (e.g. typing digits), don't mess with cursor unless formatting kicked in
            # But "1000" -> "1,000" changes text.
            
            if new_text != text:
                self.blockSignals(True) # Prevent recursive calls
                self.setText(new_text)
                self.blockSignals(False)
                
                # Restore cursor position
                new_cursor = 0
                count = 0
                for char in new_text:
                    if count == significant_chars_before:
                        # Special case: if we are strictly at the boundary of sig chars,
                        # but there are non-sig chars (like ' ' or symbol) immediately following?
                        # Usually standard strict counting works because we scan from left.
                        break
                        
                    new_cursor += 1
                    if char in "0123456789.-":
                        count += 1
                
                # If we ended exactly at the end of sig chars, new_cursor is positioned there.
                # If sig chars was 0 (start), new_cursor is usually 0.
                # If symbol is 'before', e.g. "$ 100".
                # Sig 0. Loop: new_cursor starts 0. char '$' (no match). cursor 1. char ' ' (no match). cursor 2. char '1'.
                # Wait, if sig=0, `count` starts 0. condition `count == sig` is True immediately!
                # So if loop logic check is at START of loop:
                # Loop:
                #   if count == sig: break -> breaks at 0. new_cursor = 0.
                # This positions cursor BEFORE the symbol. "$ 100" -> cursor at |$ 100.
                
                # If I want cursor AFTER symbol if I type 1st digit?
                # User types '1' into empty. Text "$ 1".
                # Cursor was at 1 (after '1'). Sig chars = 1.
                # Loop: 
                #   Start. count=0. != 1.
                #   '$': cursor=1.
                #   ' ': cursor=2.
                #   '1': count=1.
                #   Next iter: count==1 -> break. cursor=2.
                #   Cursor at "$ 1|". Correct.
                
                # This should be fine.
                
                self.setCursorPosition(new_cursor)
        
        except ValueError:
            pass
            
        self.valueChanged.emit(self.value())

    def _on_editing_finished(self):
        """Format strictly on blur."""
        self.setValue(self.value())
