import os
import platform
import sys
class FontManager:
    _font_name = "Myanmar Text" if platform.system() == "Windows" else "Noto Sans Myanmar"
    _bold_font_name = "Myanmar Text" if platform.system() == "Windows" else "Noto Sans Myanmar"

    @classmethod
    def register_fonts(cls):
        # WeasyPrint handles font loading automatically via FontConfig/System
        # We just need to ensure the font family names are correct
        pass

    @classmethod
    def get_font_family(cls):
        """Return CSS font stack"""
        if platform.system() == "Windows":
             return "'Myanmar Text', 'Myanmar MN', 'Noto Sans Myanmar', 'Pyidaungsu', sans-serif"
        else:
             return "'Noto Sans Myanmar', 'Myanmar MN', 'Pyidaungsu', sans-serif"

    @classmethod
    def get_font_name(cls):
        return cls._font_name

    @classmethod
    def get_bold_font_name(cls):
        return cls._bold_font_name
