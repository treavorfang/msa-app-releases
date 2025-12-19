import sys
import os
import configparser

# Add src/app to path
sys.path.append(os.path.join(os.getcwd(), "src", "app"))

# Test loading en.ini
config = configparser.ConfigParser(interpolation=None)
try:
    config.read('/Users/studiotai/PyProject/msa/src/app/config/languages/en.ini', encoding='utf-8')
    print("✅ Successfully loaded en.ini")
    print(f"Sections found: {config.sections()}")
    
    # Test the specific key that was causing issues
    if config.has_option('Users', 'commission_rate'):
        value = config.get('Users', 'commission_rate')
        print(f"✅ commission_rate = '{value}'")
    else:
        print("❌ commission_rate key not found")
        
except Exception as e:
    print(f"❌ Error loading en.ini: {e}")
    import traceback
    traceback.print_exc()
