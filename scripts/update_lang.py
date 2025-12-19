import os
import re
import sys
from pathlib import Path
from configparser import ConfigParser

# Determine base paths
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
APP_DIR = PROJECT_ROOT / "src" / "app"
LANG_DIR = APP_DIR / "config" / "languages"

def find_language_keys():
    """Scan all python files in src/app for language keys including f-string usage."""
    # Pattern to match self.lm.get("Key", "Default") or language_manager.get("Key", "Default")
    # Also handles single or double quotes
    # Capture group 1: Key
    # Capture group 2: Default Value
    pattern = re.compile(r'\.get\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)')
    
    keys_found = {}

    print(f"🔍 Scanning {APP_DIR} for language keys...")
    
    for py_file in APP_DIR.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = pattern.findall(content)
                for key, default_value in matches:
                    if key not in keys_found:
                        keys_found[key] = default_value
        except Exception as e:
            print(f"⚠️ Error reading {py_file}: {e}")
            
    return keys_found

def update_ini_file(language_code='en', keys=None):
    """Update the specified language INI file with missing keys."""
    if keys is None:
        keys = {}
        
    ini_path = LANG_DIR / f"{language_code}.ini"
    
    if not ini_path.exists():
        print(f"❌ Language file not found: {ini_path}")
        return

    # Use ConfigParser with case_sensitive keys = True to preserve casing if needed,
    # though usually INI section keys are case-insensitive.
    # We want to preserve comments if possible, but ConfigParser doesn't support round-trip comments well.
    # For now, we will append missing keys to the end of sections or create new sections.
    
    config = ConfigParser(interpolation=None)
    config.optionxform = str # Preserve case sensitivity of keys
    
    try:
        config.read(ini_path, encoding='utf-8')
    except Exception as e:
        print(f"❌ Error parsing {ini_path}: {e}")
        return

    added_count = 0
    updated_sections = set()

    for key, default_value in keys.items():
        if '.' in key:
            section, option = key.split('.', 1)
            # Capitalize section for consistency (e.g. Auth, Common)
            # But we should respect existing casing if section exists
            
            # Find matching section case-insensitively
            target_section = section
            for existing_section in config.sections():
                if existing_section.lower() == section.lower():
                    target_section = existing_section
                    break
            
            if not config.has_section(target_section):
                config.add_section(target_section)
                # Capitalize the first letter of the section if it is new
                if target_section.islower():
                   target_section = target_section.capitalize()
                   # Remove the lowercase one and add capitalized
                   if config.has_section(section):
                       config.remove_section(section)
                   config.add_section(target_section)
            
            if not config.has_option(target_section, option):
                config.set(target_section, option, default_value)
                added_count += 1
                updated_sections.add(target_section)
        else:
            print(f"⚠️ Skipping malformed key (no dot): {key}")

    if added_count > 0:
        with open(ini_path, 'w', encoding='utf-8') as f:
            config.write(f)
        print(f"✅ Added {added_count} missing keys to {language_code}.ini")
    else:
        print(f"✨ {language_code}.ini is up to date.")

if __name__ == "__main__":
    found_keys = find_language_keys()
    print(f"📝 Found {len(found_keys)} unique language keys in codebase.")
    
    # Update English (Source of Truth)
    update_ini_file('en', found_keys)
    
    # Optional: Update other languages with placeholders?
    # For now, we only automatically update English to ensure defaults exist.
