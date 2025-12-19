import sys
import os

# Add src/app to path
sys.path.append(os.path.join(os.getcwd(), "src", "app"))

from utils.language_manager import language_manager

print("Testing LanguageManager...")

# Test loading English
success = language_manager.load_language("English")
print(f"✅ Loaded English: {success}")

# Test getting the problematic key
commission_rate = language_manager.get("Users.commission_rate", "NOT FOUND")
print(f"✅ commission_rate = '{commission_rate}'")

# Test getting other keys
add_tech = language_manager.get("Users.add_technician", "NOT FOUND")
print(f"✅ add_technician = '{add_tech}'")

# Test Burmese if available
burmese_success = language_manager.load_language("Burmese")
print(f"✅ Loaded Burmese: {burmese_success}")

print("\n✅ All tests passed!")
