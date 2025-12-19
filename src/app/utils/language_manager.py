import configparser
import os
from pathlib import Path
from typing import Dict, List, Optional

class LanguageManager:
    _instance = None
    
    # Language code to display name mapping
    LANGUAGE_NAMES = {
        'en': 'English',
        'my': 'Burmese - ဗမာ',
        'zh': 'Chinese (Simplified) - 简体中文',
        'hi': 'Hindi - हिंदी',
        'ja': 'Japanese - 日本語',
        'ko': 'Korean - 한국어',
        'th': 'Thai - ไทย',
        'vi': 'Vietnamese - Tiếng Việt'
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LanguageManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.languages_dir = os.path.join(Path(__file__).parent.parent, "config", "languages")
        os.makedirs(self.languages_dir, exist_ok=True)
        
        self.current_language = "en"  # Default to English language code
        self.translations: Dict[str, str] = {}
        self._initialized = True
        
    def get_available_languages(self) -> List[Dict[str, str]]:
        """Get list of available languages with their codes and display names"""
        languages = []
        if os.path.exists(self.languages_dir):
            for file in os.listdir(self.languages_dir):
                if file.endswith(".ini"):
                    code = file.replace(".ini", "")
                    display_name = self.LANGUAGE_NAMES.get(code, code.upper())
                    languages.append({
                        'code': code,
                        'name': display_name
                    })
        return sorted(languages, key=lambda x: x['name'])
    
    def load_language(self, language_code: str) -> bool:
        """Load translations for a specific language code (e.g., 'en', 'my')"""
        self.current_language = language_code
        self.translations = {}
        
        file_path = os.path.join(self.languages_dir, f"{language_code}.ini")
        
        if os.path.exists(file_path):
            try:
                config = configparser.ConfigParser(interpolation=None)
                config.read(file_path, encoding='utf-8')
                
                for section in config.sections():
                    for key, value in config.items(section):
                        # Handle escaped newlines
                        self.translations[f"{section.lower()}.{key}"] = value.replace('\\n', '\n')
                
                print(f"✅ Loaded language: {self.LANGUAGE_NAMES.get(language_code, language_code)}")
                return True
            except Exception as e:
                print(f"Error loading language {language_code}: {e}")
                return False
        else:
            print(f"⚠️ Language file not found: {file_path}")
            return False
    
    def get(self, key: str, default: str = None) -> str:
        """Get translated string"""
        return self.translations.get(key.lower(), default or key)
    
    def get_language_name(self, code: str = None) -> str:
        """Get display name for a language code"""
        if code is None:
            code = self.current_language
        return self.LANGUAGE_NAMES.get(code, code.upper())

# Global instance
language_manager = LanguageManager()
