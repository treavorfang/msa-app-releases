import firebase_admin
from firebase_admin import credentials, firestore
import functions_framework
import datetime
import json
import hashlib
import os
import binascii

# Initialize Firebase Admin SDK
# (In Cloud Functions, credential is auto-detected)
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()

def cors_headers(request):
    """Set CORS headers for the response."""
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600'
    }
    return headers

def handle_options(request):
    """Handle CORS pre-flight OPTIONS request."""
    headers = cors_headers(request)
    return ('', 204, headers)

# --- Security Utilities ---
def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')[:32]
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:32]
    stored_password = stored_password[32:]
    pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt.encode('ascii'), 100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password

@functions_framework.http
def api_handler(request):
    """
    Main Entry Point for MSA Cloud API
    Handles: /register_device, /login_lock_check, /check_license
    """
    # 1. CORS Headers
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}

    # 2. Parse Request
    try:
        data = request.get_json(silent=True)
        if not data:
             return (json.dumps({"error": "Invalid JSON"}), 400, headers)
    except Exception as e:
        return (json.dumps({"error": f"JSON Error: {str(e)}"}), 400, headers)

    path = request.path
    
    # -----------------------------------------------
    # ENDPOINT: REGISTER DEVICE (New Account)
    # -----------------------------------------------
    if path == '/register_device' or 'register' in path:
        email = data.get('email')
        password = data.get('password')
        hwid = data.get('hwid')
        name = data.get('name', 'User')

        phone = data.get('phone', '')
        city = data.get('city', '')
        country = data.get('country', '')

        if not email or not password or not hwid:
             return (json.dumps({"error": "Missing fields"}), 400, headers)

        # Check if user exists
        user_ref = db.collection('users').document(email)
        doc = user_ref.get()
        if doc.exists:
             return (json.dumps({"error": "User already exists"}), 409, headers)

        # HASH PASSWORD
        hashed_pw = hash_password(password)

        # Create User with PENDING status
        user_data = {
            "email": email,
            "password": hashed_pw, # SECURE STORE
            "hwid": hwid, 
            "status": "pending", # Requires Admin Approval
            "role": "user",
            "created_at": firestore.SERVER_TIMESTAMP,
            "last_login": firestore.SERVER_TIMESTAMP,
            "name": name,
            "phone": phone,
            "city": city,
            "country": country
        }
        user_ref.set(user_data)
        
        return (json.dumps({"success": True, "message": "Registered. Status: Pending Approval"}), 200, headers)

    # -----------------------------------------------
    # ENDPOINT: LOGIN & LOCK CHECK
    # -----------------------------------------------
    elif path == '/login_lock_check' or 'login' in path:
        email = data.get('email')
        password = data.get('password')
        hwid = data.get('hwid')

        if not email or not password or not hwid:
             return (json.dumps({"error": "Missing fields"}), 400, headers)

        user_ref = db.collection('users').document(email)
        doc = user_ref.get()
        
        if not doc.exists:
             return (json.dumps({"error": "User not found"}), 404, headers)
        
        user_data = doc.to_dict()
        
        # VERIFY PASSWORD
        stored_pw = user_data.get('password', '')
        # Handle backward compatibility with old plain text passwords if necessary
        # But for new system, assume hash. 
        if len(stored_pw) > 32 and verify_password(stored_pw, password):
             pass # Match!

        else:
             # Log Failure
             try:
                 db.collection('audit_log').add({
                     "event": "login_attempt", "email": email, "hwid": hwid,
                     "timestamp": firestore.SERVER_TIMESTAMP, "ip": request.remote_addr,
                     "status": "failed", "reason": "Invalid Password"
                 })
             except: pass
             return (json.dumps({"error": "Invalid Password"}), 401, headers)

        # CHECK STATUS
        status = user_data.get('status', 'pending')
        if status != 'active':
             # Log Failure
             try:
                 db.collection('audit_log').add({
                     "event": "login_attempt", "email": email, "hwid": hwid,
                     "timestamp": firestore.SERVER_TIMESTAMP, "ip": request.remote_addr,
                     "status": "failed", "reason": f"Account {status}"
                 })
             except: pass
             return (json.dumps({"error": f"Account Status: {status}"}), 403, headers)
        
        # CHECK HWID LOCK
        registered_hwid = user_data.get('hwid')
        if registered_hwid != hwid:
             # Log Failure
             try:
                 db.collection('audit_log').add({
                     "event": "login_attempt", "email": email, "hwid": hwid,
                     "timestamp": firestore.SERVER_TIMESTAMP, "ip": request.remote_addr,
                     "status": "failed", "reason": "HWID Mismatch"
                 })
             except: pass
             return (json.dumps({"error": "HWID Mismatch. License locked to another device."}), 403, headers)

        # SUCCESS
        # Audit Log
        try:
             db.collection('audit_log').add({
                 "event": "login",
                 "email": email,
                 "hwid": hwid,
                 "timestamp": firestore.SERVER_TIMESTAMP,
                 "ip": request.remote_addr,
                 "status": "success",
                 "license_type": user_data.get('license_type', 'N/A'),
                 "expiration_date": user_data.get('expiration_date', 'N/A')
             })
        except Exception as e:
             print(f"Log Error: {e}")

        # Update Last Login
        try:
            user_ref.update({"last_login": firestore.SERVER_TIMESTAMP})
        except Exception as e:
            print(f"Update Error: {e}")

        # Generate a Session Token (For now, use User ID/Email as simple token)
        return (json.dumps({
            "valid": True,
            "status": "active",
            "token": email, # Client stores this
            "details": {
                "name": user_data.get('name'),
                "email": email,
                "role": user_data.get('role'),
                "expiration_date": user_data.get('expiration_date'), # Pass expiry to client
                "license_type": user_data.get('license_type')
            }
        }), 200, headers)

    # -------------------------------------------------------------------------
    # ROUTE: /check_license (Silent Startup Check)
    # -------------------------------------------------------------------------
    elif path.endswith("/check_license"):
        # Here 'license_key' is actually the user document ID (token) we saved
        token = data.get("license_key") 
        hwid = data.get("hwid")

        if not token:
            return ({"error": "No token"}, 400, headers)

        try:
            doc_ref = db.collection("users").document(token)
            doc = doc_ref.get()
            if not doc.exists:
                return ({"error": "Invalid Session"}, 401, headers)
            
            user_data = doc.to_dict()
            
            # Re-verify HWID
            if user_data.get("hwid") != hwid:
                return ({"error": "Device Mismatch"}, 403, headers)

            # Re-verify Status
            if user_data.get("status") != "active":
                return ({"error": "Account Suspended"}, 403, headers)

            return ({
                "status": "active",
                "name": user_data.get("name"),
                "expiry": user_data.get("expiration_date", "Lifetime"),
                "expiration_date": user_data.get("expiration_date"),
                "license_type": user_data.get("license_type")
            }, 200, headers)

        except Exception as e:
            return ({"error": str(e)}, 500, headers)

    # -------------------------------------------------------------------------
    # Fallback
    # -------------------------------------------------------------------------
    return ({"error": "Unknown Endpoint"}, 404, headers)
