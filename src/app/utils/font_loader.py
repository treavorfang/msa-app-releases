"""
Font loader for the MSA application.
Loads custom fonts from the static/fonts directory to ensure consistent
typography across all platforms (macOS, Windows, Linux).
"""

import os
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication


class FontLoader:
    """Handles loading of custom application fonts."""
    
    _fonts_loaded = False
    _font_families = []
    
    @classmethod
    def load_fonts(cls):
        """
        Load all custom fonts from the static/fonts directory.
        Should be called once during application initialization.
        
        Returns:
            list: List of loaded font family names
        """
        if cls._fonts_loaded:
            return cls._font_families
        
        # Get the fonts directory path
        # Navigate from utils/ up to app/, then to static/fonts
        current_dir = os.path.dirname(os.path.abspath(__file__))  # utils/
        app_dir = os.path.dirname(current_dir)  # app/
        fonts_dir = os.path.join(app_dir, 'static', 'fonts')
        
        if not os.path.exists(fonts_dir):
            print(f"Warning: Fonts directory not found at {fonts_dir}")
            cls._fonts_loaded = True
            return cls._font_families
        
        # Load all .ttf and .otf files
        font_extensions = ('.ttf', '.otf', '.ttc')
        loaded_count = 0
        
        for filename in os.listdir(fonts_dir):
            if filename.lower().endswith(font_extensions):
                font_path = os.path.join(fonts_dir, filename)
                font_id = QFontDatabase.addApplicationFont(font_path)
                
                if font_id != -1:
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    cls._font_families.extend(families)
                    loaded_count += 1
                    print(f"Loaded font: {filename} -> {families}")
                else:
                    print(f"Warning: Failed to load font: {filename}")
        
        print(f"Successfully loaded {loaded_count} font file(s)")
        cls._fonts_loaded = True
        return cls._font_families
    
    @classmethod
    def get_primary_font_family(cls):
        """
        Get the primary font family name for the application.
        
        Returns:
            str: Font family name, defaults to 'Inter' if available
        """
        if not cls._fonts_loaded:
            cls.load_fonts()
        
        # Check if Inter is available
        if 'Inter' in cls._font_families or 'Inter Variable' in cls._font_families:
            return 'Inter'
        
        # Fallback to first loaded font or system default
        if cls._font_families:
            return cls._font_families[0]
        
        return 'Segoe UI'  # System default fallback
    
    @classmethod
    def set_application_font(cls, point_size=10):
        """
        Set the application-wide default font.
        
        Args:
            point_size: Font size in points (default: 10)
        """
        from PySide6.QtGui import QFont
        
        if not cls._fonts_loaded:
            cls.load_fonts()
        
        font_family = cls.get_primary_font_family()
        app_font = QFont(font_family, point_size)
        
        app = QApplication.instance()
        if app:
            app.setFont(app_font)
            print(f"Set application font to: {font_family} {point_size}pt")
