"""
License history management (Database Wrapper)
"""
import os
from typing import List, Dict, Any
from .config import HISTORY_FILE_PATH, LIFETIME_EXPIRY, EXPIRING_SOON_DAYS
from .database import LicenseDatabase

class HistoryManager:
    """Manages license history using SQLite"""
    
    def __init__(self):
        self.db = LicenseDatabase()
        self._migrate_csv()
        
    def _migrate_csv(self):
        """Migrate existing CSV if needed"""
        if os.path.exists(HISTORY_FILE_PATH):
            count = self.db.import_from_csv(HISTORY_FILE_PATH)
            if count > 0:
                print(f"Migrated {count} records from CSV to Database.")

    def save_license(self, license_data: dict):
        """Save a generated license to history"""
        try:
            self.db.add_license(license_data)
            print(f"✓ License saved to database: {license_data.get('customer_name', 'Unknown')}")
        except Exception as e:
            print(f"Warning: Failed to save license to database: {e}")
    
    def load_history(self) -> List[List[str]]:
        """
        Load all license history in UI-compatible format
        Returns [Headers, *Rows]
        """
        raw_data = self.db.get_all_licenses()
        
        if not raw_data:
            return []
            
        # raw_data[0] are DB column names (lowercase with underscores)
        # We want to map them to friendly names for UI
        
        db_headers = raw_data[0]
        friendly_map = {
            'generated_at': 'Generated Date',
            'customer_name': 'Customer Name',
            'email': 'Email',
            'phone': 'Phone',
            'city': 'City',
            'country': 'Country',
            'hwid': 'HWID',
            'expiry_date': 'Expiry Date',
            'license_key': 'License Key',
            'license_type': 'License Type',
            'invoice_number': 'Invoice Number',
            'amount': 'Amount',
            'payment_method': 'Payment Method',
            'payment_status': 'Payment Status',
            'renewal_reminder': 'Renewal Reminder',
            'notes': 'Notes',
            'id': 'ID'
        }
        
        # Transform headers
        headers = [friendly_map.get(col, col) for col in db_headers]
        
        # Filter out ID if we want to mimic CSV closely, but ID is useful.
        # Let's keep ID but formatting is key.
        
        # Transform rows (convert None to "")
        rows = []
        for row in raw_data[1:]:
            rows.append([str(val) if val is not None else "" for val in row])
            
        return [headers] + rows
    
    def delete_entry(self, identifier: Any) -> bool:
        """
        Delete a license entry
        identifier: Can be row_index (int) or license_key (str)
        """
        # If identifier is string, assume it's the key
        if isinstance(identifier, str):
            return self.db.delete_license(identifier)
            
        # If int, assume row index (legacy support)
        if isinstance(identifier, int):
            data = self.load_history()
            target_row_idx = identifier + 1
            if target_row_idx >= len(data):
                return False
                
            row = data[target_row_idx]
            headers = data[0]
            
            try:
                key_idx = headers.index('License Key')
                key = row[key_idx]
                return self.db.delete_license(key)
            except ValueError:
                return False
                
        return False

    def calculate_statistics(self, data: List[List[str]]) -> Dict[str, int]:
        """Calculate statistics from history data"""
        if len(data) <= 1:
            return {'total': 0, 'active': 0, 'expiring': 0, 'expired': 0, 'lifetime': 0}
        
        total = len(data) - 1
        active = 0
        expiring = 0
        expired = 0
        lifetime = 0
        
        headers = data[0]
        try:
            expiry_idx = headers.index('Expiry Date')
        except ValueError:
             # If not found, look for 'expiry_date'
            try:
                expiry_idx = headers.index('expiry_date')
            except ValueError:
                return {'total': total, 'active': 0, 'expiring': 0, 'expired': 0, 'lifetime': 0}

        for row in data[1:]:  # Skip header
            if len(row) > expiry_idx:
                expiry_date_str = row[expiry_idx]
                
                if expiry_date_str == LIFETIME_EXPIRY:
                    lifetime += 1
                    active += 1
                else:
                    try:
                        expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
                        today = datetime.now()
                        days_until_expiry = (expiry_date - today).days
                        
                        if days_until_expiry < 0:
                            expired += 1
                        elif days_until_expiry <= EXPIRING_SOON_DAYS:
                            expiring += 1
                            active += 1
                        else:
                            active += 1
                    except:
                        pass
        
        return {
            'total': total,
            'active': active,
            'expiring': expiring,
            'expired': expired,
            'lifetime': lifetime
        }
    
    def get_expiry_status(self, expiry_date_str: str) -> str:
        """Get status string"""
        if not expiry_date_str:
            return 'unknown'
        
        if expiry_date_str == LIFETIME_EXPIRY:
            return 'lifetime'
        
        try:
            expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
            today = datetime.now()
            days_until_expiry = (expiry_date - today).days
            
            if days_until_expiry < 0:
                return 'expired'
            elif days_until_expiry <= EXPIRING_SOON_DAYS:
                return 'expiring'
            else:
                return 'active'
        except:
            return 'unknown'
