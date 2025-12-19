# src/app/config/config_loader.py
import os
from typing import Dict, List

def load_ini_config(file_path: str) -> Dict[str, List[str]]:
    """
    Load INI-style configuration file into a dictionary
    
    Args:
        file_path: Path to the config file
        
    Returns:
        Dictionary with sections as keys and lists of values
    """
    config_data = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            current_section = None
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Section header
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                    config_data[current_section] = []
                # Value line
                elif current_section is not None:
                    config_data[current_section].append(line)
                    
    except FileNotFoundError:
        print(f"Warning: Config file not found: {file_path}")
        return {}
    except Exception as e:
        print(f"Error loading config file {file_path}: {e}")
        return {}
    
    return config_data

def load_brands_config() -> Dict[str, List[str]]:
    """Load phone brands and models configuration"""
    from .config import BRANDS_CONFIG_PATH
    return load_ini_config(BRANDS_CONFIG_PATH)

def load_phone_errors() -> Dict[str, List[str]]:
    """Load phone error categories configuration"""
    from .config import PHONE_ERRORS_CONFIG_PATH
    
    error_categories = load_ini_config(PHONE_ERRORS_CONFIG_PATH)
    
    # Fallback if file can't be loaded or is empty
    if not error_categories:
        error_categories = {
            "Power/Boot": ["No Power", "Won't Turn On", "Bootloop"],
            "Display": ["No Display", "Touchscreen Not Working"],
            "Battery": ["Battery Drain", "Not Charging", "Overheating"],
            "Connectivity": ["No WiFi", "Bluetooth Issues", "No Signal"]
        }
        print("Using fallback phone error categories")
    
    return error_categories