# src/app/services/license_service.py
"""
License Service - Handles online license activation and verification via Firebase.
Enforces hardware locking (HWID) to prevent multi-device usage.
"""

import platform
import hashlib
import json
import base64
import os
import subprocess
import requests # Requires: pip install requests
from datetime import datetime
import functools

from config.config import BASE_DIR, USER_DATA_DIR

# Firebase Cloud Function URL (Replace with your actual endpoint)
FIREBASE_API_URL = "https://api-249367424234.asia-southeast1.run.app"

LICENSE_FILE_PATH = os.path.join(USER_DATA_DIR, "license.key") # Stores just the key/token now

class LicenseService:
    def __init__(self):
        self._license_data = None
        self._is_active = False
        
    @functools.lru_cache(maxsize=1)
    def get_fingerprint_details(self) -> dict:
        """
        Get the components used for generating the machine fingerprint.
        Cached to prevent repeated expensive subprocess calls.
        """
        import uuid
        
        # 1. Get System UUID (Most Secure/Stable)
        system_uuid = ""
        try:
            if platform.system() == 'Darwin':
                # macOS: Get IOPlatformUUID
                cmd = "ioreg -d2 -c IOPlatformExpertDevice | awk -F\\\" '/IOPlatformUUID/{print $(NF-1)}'"
                try:
                    system_uuid = subprocess.check_output(cmd, shell=True).decode().strip()
                except subprocess.CalledProcessError:
                    pass
            elif platform.system() == 'Windows':
                # Windows: Get CSPRODUCT UUID
                cmd = "wmic csproduct get uuid"
                try:
                    output = subprocess.check_output(cmd, shell=True).decode()
                    # Typical output: UUID \n XXXXX-XXXX...
                    lines = [line.strip() for line in output.split('\n') if line.strip()]
                    if len(lines) > 1:
                        system_uuid = lines[1]
                except subprocess.CalledProcessError:
                    pass
            elif platform.system() == 'Linux':
                # Linux: Get machine-id
                for p in ['/etc/machine-id', '/var/lib/dbus/machine-id']:
                    if os.path.exists(p):
                        with open(p, 'r') as f:
                            system_uuid = f.read().strip()
                        break
        except Exception as e:
            print(f"Warning: Failed to retrieve system UUID: {e}")

        # 2. Get MAC Address
        mac_addr = str(uuid.getnode())

        # 3. System Info
        sys_info = f"{platform.system()}-{platform.machine()}-{platform.processor()}"
        
        # Combine Entropy
        if system_uuid:
            raw_id = f"{system_uuid}-{sys_info}"
        else:
            raw_id = f"{mac_addr}-{sys_info}-fallback"
            
        return {
            "system_uuid": system_uuid if system_uuid else "N/A",
            "mac_address": mac_addr,
            "platform": sys_info,
            "raw_id": raw_id
        }

    def get_machine_fingerprint(self) -> str:
        """Generate a secure unique identifier for the current machine."""
        details = self.get_fingerprint_details()
        fingerprint = hashlib.sha256(details['raw_id'].encode()).hexdigest()
        return fingerprint.upper()[:16]

    def _validate_expiry(self, data: dict) -> tuple:
        """Check if license data has expired. Returns (bool, message)"""
        # 1. Check strict status
        if data.get('status') != 'active':
            return False, f"Account Status: {data.get('status', 'unknown')}"
            
        # 2. Check Expiry Date
        expiry_str = data.get('expiration_date')
        
        # If no expiry date is set, it means no subscription plan -> Invalid
        if not expiry_str:
             return False, "No subscription plan found."
             
        if expiry_str.lower() != 'lifetime':
            try:
                exp_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                days_left = (exp_date - datetime.now().date()).days
                
                if days_left < 0:
                    return False, f"License expired on {expiry_str}. Please renew."
            except ValueError:
                return False, "Invalid expiration date format."
                
        return True, "Active"

    def _post_request(self, endpoint: str, data: dict, timeout: int = 10) -> dict:
        """Helper to handle network requests uniformly"""
        try:
            response = requests.post(
                f"{FIREBASE_API_URL}{endpoint}",
                json=data,
                timeout=timeout
            )
            
            if response.status_code in [200, 201]:
                try:
                    return {"success": True, "data": response.json()}
                except ValueError:
                    return {"success": False, "message": f"Server Error (Invalid JSON): {response.text[:100]}"}
            
            # Handle Errors
            msg = "Request Failed"
            try:
                msg = response.json().get("error", response.text or msg)
            except:
                msg = response.text or msg
            
            return {"success": False, "message": msg, "status_code": response.status_code}
            
        except requests.exceptions.ConnectionError:
            return {"success": False, "message": "Connection Failed. Internet required."}
        except Exception as e:
            return {"success": False, "message": f"Network Error: {str(e)}"}

    def check_online_status(self) -> dict:
        """Validate license key against Firebase."""
        if not os.path.exists(LICENSE_FILE_PATH):
            return {"valid": False, "message": "No license found"}
            
        try:
            with open(LICENSE_FILE_PATH, 'r') as f:
                license_key = f.read().strip()
            
            if not license_key:
                return {"valid": False, "message": "Empty license file"}

            hwid = self.get_machine_fingerprint()
            
            result = self._post_request("/check_license", {"license_key": license_key, "hwid": hwid}, timeout=5)
            
            if result['success']:
                data = result['data']
                
                # Validate Status & Expiry
                is_valid, msg = self._validate_expiry(data)
                
                if is_valid:
                    self._is_active = True
                    self._license_data = data
                    return {"valid": True, "message": "Active", "details": data}
                else:
                    return {"valid": False, "message": msg}
            else:
                return {"valid": False, "message": result['message']}

        except Exception as e:
            return {"valid": False, "message": f"Error: {str(e)}"}

    def login_online(self, email: str, password: str, hwid: str) -> dict:
        """Authenticate user with Firebase and check HWID lock."""
        result = self._post_request("/login_lock_check", {
            "email": email, 
            "password": password, 
            "hwid": hwid
        })
        
        if result['success']:
            data = result['data']
            
            if data.get('status') == 'active':
                # Validate Expiry
                # Login response puts expiration_date inside 'details' dict
                validation_data = data.get('details', data)
                # Ensure status is available for validation if it's not in details
                if 'status' not in validation_data:
                    validation_data['status'] = data.get('status')
                    
                is_valid, msg = self._validate_expiry(validation_data)
                
                if not is_valid:
                    return {"valid": False, "message": msg}
                
                token = data.get('token', '') 
                try:
                    with open(LICENSE_FILE_PATH, 'w') as f:
                        f.write(token)
                except IOError as e:
                     return {"valid": False, "message": f"Failed to save license: {e}"}
                    
                self._is_active = True
                return {"valid": True, "message": "Active", "details": data}
                
            elif data.get('status') == 'pending':
                return {"valid": False, "message": "Account is Pending Approval."}
            else:
                return {"valid": False, "message": "Account Suspended or Unknown."}
        
        return {"valid": False, "message": result['message']}

    def register_online(self, email: str, password: str, hwid: str, name: str = "User", phone: str = "", city: str = "", country: str = "") -> dict:
        """Register a new account (Pending status)."""
        result = self._post_request("/register_device", {
            "email": email, 
            "password": password, 
            "hwid": hwid,
            "name": name,
            "phone": phone,
            "city": city,
            "country": country
        })
        
        if result['success']:
            return {"success": True, "message": "Registered"}
        else:
            return {"success": False, "message": result['message']}
