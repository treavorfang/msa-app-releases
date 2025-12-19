
"""
Simple Firebase Admin Wrapper for Online License Management.
Requires: serviceAccountKey.json
"""
import firebase_admin
from firebase_admin import credentials, firestore, auth
import threading
import logging
import os

class OnlineManager:
    _instance = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OnlineManager, cls).__new__(cls)
            cls._instance._init_firebase()
        return cls._instance
    
    def _init_firebase(self):
        """Initialize connection with serviceAccountKey.json"""
        if not firebase_admin._apps:
            try:
                import sys
                if getattr(sys, 'frozen', False):
                    # Running in a PyInstaller bundle
                    base_dir = sys._MEIPASS
                else:
                    # Running from source
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
                key_path = os.path.join(base_dir, "serviceAccountKey.json")
                
                cred = credentials.Certificate(key_path)
                firebase_admin.initialize_app(cred)
                self._db = firestore.client()
                print(f"Firebase Admin Initialized with key: {key_path}")
            except Exception as e:
                print(f"Failed to init Firebase: {e}")
                self._db = None
    
    def get_users(self, status_filter=None):
        """Fetch users, optionally filtered by status ('pending', 'active')"""
        if not self._db:
            return []
        
        try:
            # DEBUG: Print all collections to find the right one
            cols = self._db.collections()
            print("DEBUG: Found Collections:", [c.id for c in cols])

            users_ref = self._db.collection('users')
            
            if status_filter:
                query = users_ref.where('status', '==', status_filter)
            else:
                query = users_ref
                
            docs = query.stream()
            result = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                result.append(data)
            return result
        except Exception as e:
            print(f"Error fetching users: {e}")
            return []
            
    def update_status(self, doc_id, new_status, additional_data=None):
        """
        Update user status (e.g. pending -> active).
        Also, if invoice details are present, save them to a specialized 'invoices' collection
        to keep a clean financial history.
        """
        if not self._db:
            return False
            
        try:
            # 1. Prepare User Update Payload (Exclude invoice_details)
            users_ref = self._db.collection('users').document(doc_id)
            update_payload = {'status': new_status}
            
            invoice_payload = None
            if additional_data:
                # Create a copy to manipulate
                data_copy = additional_data.copy()
                
                # Extract invoice details if present
                if 'invoice_details' in data_copy:
                    invoice_payload = data_copy.pop('invoice_details')
                    
                # Update user with remaining data (expiry, license_type, etc.)
                update_payload.update(data_copy)
            
            users_ref.update(update_payload)
            
            # 2. Save Invoice Record (If applicable)
            if invoice_payload:
                inv_data = invoice_payload.copy()
                # Enriched with meta-data
                inv_data['user_email'] = doc_id
                inv_data['created_at'] = additional_data.get('activated_at', firestore.SERVER_TIMESTAMP)
                inv_data['license_type'] = additional_data.get('license_type', 'N/A')
                inv_data['expiration_date'] = additional_data.get('expiration_date', 'N/A')
                
                # Create separate collection 'invoices'
                # Use Invoice Number as Doc ID if available, else auto
                invoice_number = inv_data.get('invoice_number')
                if invoice_number:
                     self._db.collection('invoices').document(invoice_number).set(inv_data)
                else:
                     self._db.collection('invoices').add(inv_data)
                     
            return True
        except Exception as e:
            print(f"Update failed: {e}")
            return False

    def delete_user(self, doc_id):
        if not self._db: return False
        try:
            self._db.collection('users').document(doc_id).delete()
            return True
        except:
            return False

    def get_user(self, user_id):
        """Fetch a single user document by ID (email or uid). Tries ID first, then email query."""
        if not self._db or not user_id: return None
        try:
            # 1. Try Direct ID Lookup
            doc = self._db.collection('users').document(user_id).get()
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            
            # 2. Try Email Query Lookup
            # If user_id looks like an email, try to find it in 'email' field
            if '@' in user_id:
                users_ref = self._db.collection('users')
                query = users_ref.where('email', '==', user_id).limit(1).stream()
                for q_doc in query:
                    data = q_doc.to_dict()
                    data['id'] = q_doc.id
                    return data
                    
            return None
        except Exception as e:
            print(f"Error fetching user {user_id}: {e}")
            return None

    def get_invoices(self):
        """Fetch all invoices orders by creation time"""
        if not self._db: return []
        try:
            ref = self._db.collection('invoices')
            # Sort by created_at desc if possible
            docs = ref.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
            return [dict(d.to_dict(), id=d.id) for d in docs]
        except Exception as e:
            print(f"Error fetching invoices: {e}")
            return []

    def get_audit_logs(self, limit=50):
        """Fetch recent audit logs"""
        if not self._db: return []
        try:
            ref = self._db.collection('audit_log')
            docs = ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream()
            return [dict(d.to_dict(), id=d.id) for d in docs]
        except Exception as e:
            print(f"Error fetching audit logs: {e}")
            return []

    def get_last_invoice_number(self):
        """Get the last generated invoice number from Firebase"""
        if not self._db: return None
        try:
            # Try to get latest by created_at
            ref = self._db.collection('invoices')
            docs = ref.order_by('created_at', direction=firestore.Query.DESCENDING).limit(1).stream()
            for doc in docs:
                return doc.to_dict().get('invoice_number')
            return None
        except Exception:
            return None

    def save_manual_invoice(self, data):
        """Save a manually generated license invoice to Firebase"""
        if not self._db: return False
        try:
            # Use invoice number as document ID
            invoice_number = data.get('invoice_number')
            if not invoice_number:
                return False
                
            # Add timestamp if missing
            if 'created_at' not in data:
                data['created_at'] = firestore.SERVER_TIMESTAMP
                
            self._db.collection('invoices').document(invoice_number).set(data)
            return True
        except Exception as e:
            print(f"Failed to save manual invoice: {e}")
            return False
