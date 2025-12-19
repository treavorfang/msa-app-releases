"""
Database management for License Generator (SQLite) - Normalized Schema
"""
import sqlite3
import csv
import os
from datetime import datetime
from .config import PERSISTENT_DIR

DB_DIR = os.path.join(PERSISTENT_DIR, "database")
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR, exist_ok=True)
DB_FILE = os.path.join(DB_DIR, "licenses.db")

class LicenseDatabase:
    def __init__(self):
        self.db_file = DB_FILE
        self._init_db()
        self._migrate_schema()
    
    def _connect(self):
        return sqlite3.connect(self.db_file)
    
    def _init_db(self):
        """Initialize database with normalized schema"""
        conn = self._connect()
        cursor = conn.cursor()
        
        # 1. Customers Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                city TEXT,
                country TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted INTEGER DEFAULT 0
            )
        ''')

        # 2. Licenses Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                hwid TEXT NOT NULL,
                license_key TEXT UNIQUE,
                license_type TEXT,
                expiry_date TEXT,
                generated_at TIMESTAMP,
                renewal_reminder TEXT,
                notes TEXT,
                is_deleted INTEGER DEFAULT 0,
                FOREIGN KEY(customer_id) REFERENCES customers(id)
            )
        ''')

        # 3. Invoices Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_id INTEGER,
                invoice_number TEXT,
                amount TEXT,
                currency TEXT,
                payment_method TEXT,
                payment_status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted INTEGER DEFAULT 0,
                FOREIGN KEY(license_id) REFERENCES licenses(id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def _migrate_schema(self):
        """Migrate flat table to normalized schema if needed"""
        conn = self._connect()
        cursor = conn.cursor()
        
        # Check if old table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='licenses_flat'")
        if cursor.fetchone():
            conn.close()
            return # Already renamed or migrated?

        # Check if we have the old 'licenses' table with the flat schema
        # We can check for a column that shouldn't exists in new schema, e.g. customer_name
        cursor.execute("PRAGMA table_info(licenses)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'customer_name' in columns:
            print("Migrating database to normalized schema...")
            # Rename old table
            cursor.execute("ALTER TABLE licenses RENAME TO licenses_flat")
            conn.commit()
            
            # Create new tables
            self._init_db()
            
            # Move Data
            cursor.execute("SELECT * FROM licenses_flat")
            flat_rows = cursor.fetchall()
            col_map = {col: i for i, col in enumerate(columns)}
            
            for row in flat_rows:
                # Helper to get val
                get = lambda c: row[col_map[c]] if c in col_map else None
                
                # 1. Insert Customer
                cursor.execute("INSERT INTO customers (name, email, phone, city, country) VALUES (?, ?, ?, ?, ?)",
                               (get('customer_name'), get('email'), get('phone'), get('city'), get('country')))
                cust_id = cursor.lastrowid
                
                # 2. Insert License
                cursor.execute("INSERT INTO licenses (customer_id, hwid, license_key, license_type, expiry_date, generated_at, renewal_reminder, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                               (cust_id, get('hwid'), get('license_key'), get('license_type'), get('expiry_date'), get('generated_at'), get('renewal_reminder'), get('notes')))
                lic_id = cursor.lastrowid
                
                # 3. Insert Invoice
                # Extract currency/amount logic if needed, simplify for now
                cursor.execute("INSERT INTO invoices (license_id, invoice_number, amount, payment_method, payment_status) VALUES (?, ?, ?, ?, ?)",
                               (lic_id, get('invoice_number'), get('amount'), get('payment_method'), get('payment_status')))
            
            conn.commit()
            print("Migration complete.")
            
        conn.close()

    def add_license(self, data: dict):
        """Add a new license (Transactional insert across 3 tables)"""
        conn = self._connect()
        cursor = conn.cursor()
        
        try:
            # 1. Insert Customer
            cursor.execute("INSERT INTO customers (name, email, phone, city, country) VALUES (?, ?, ?, ?, ?)",
                           (data.get('customer_name'), data.get('email'), data.get('phone'), data.get('city'), data.get('country')))
            customer_id = cursor.lastrowid
            
            # 2. Insert License
            cursor.execute('''
                INSERT INTO licenses (customer_id, hwid, license_key, license_type, expiry_date, generated_at, renewal_reminder, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                customer_id,
                data.get('hwid'),
                data.get('license_key'),
                data.get('license_type'),
                data.get('expiry_date'),
                data.get('generated_at'),
                data.get('renewal_reminder'),
                data.get('notes')
            ))
            license_id = cursor.lastrowid
            
            # 3. Insert Invoice
            cursor.execute('''
                INSERT INTO invoices (license_id, invoice_number, amount, payment_method, payment_status)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                license_id,
                data.get('invoice_number'),
                data.get('amount'),
                data.get('payment_method'),
                data.get('payment_status')
            ))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_all_licenses(self):
        """Get all licenses (JOINED) - flat structure for UI"""
        conn = self._connect()
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                l.generated_at,
                c.name as customer_name,
                c.email,
                c.phone,
                c.city,
                c.country,
                l.hwid,
                l.expiry_date,
                l.license_key,
                l.license_type,
                i.invoice_number,
                i.amount,
                i.payment_method,
                i.payment_status,
                l.renewal_reminder,
                l.notes,
                l.id as license_id
            FROM licenses l
            JOIN customers c ON l.customer_id = c.id
            JOIN invoices i ON i.license_id = l.id
            WHERE l.is_deleted = 0
            ORDER BY l.id DESC
        '''
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Manually define columns to match previous schema order for consistency
        columns = [
            'generated_at', 'customer_name', 'email', 'phone', 'city', 'country',
            'hwid', 'expiry_date', 'license_key', 'license_type', 'invoice_number',
            'amount', 'payment_method', 'payment_status', 'renewal_reminder', 'notes', 'id'
        ]
        
        formatted_rows = [list(row) for row in rows]
        
        conn.close()
        return [columns] + formatted_rows

    def delete_license(self, license_key):
        """Soft delete a license by key"""
        conn = self._connect()
        cursor = conn.cursor()
        
        # Soft delete license
        cursor.execute('UPDATE licenses SET is_deleted = 1 WHERE license_key = ?', (license_key,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def import_from_csv(self, csv_path):
        """Import legacy CSV data (mapped to new schema)"""
        if not os.path.exists(csv_path):
            return 0
        
        # Check if we already have data
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT Count(*) FROM licenses")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return 0 # Skip import if DB not empty
        conn.close()

        count = 0
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    data = {
                        'generated_at': row.get('Generated Date'),
                        'customer_name': row.get('Customer Name'),
                        'email': row.get('Email'),
                        'phone': row.get('Phone'),
                        'city': row.get('City', row.get('Company', '')),
                        'country': row.get('Country'),
                        'hwid': row.get('HWID'),
                        'expiry_date': row.get('Expiry Date'),
                        'license_key': row.get('License Key'),
                        'license_type': row.get('License Type'),
                        'invoice_number': row.get('Invoice Number'),
                        'amount': row.get('Amount'),
                        'payment_method': row.get('Payment Method'),
                        'payment_status': row.get('Payment Status'),
                        'renewal_reminder': row.get('Renewal Reminder'),
                        'notes': row.get('Notes')
                    }
                    try:
                        self.add_license(data)
                        count += 1
                    except Exception as e:
                        print(f"Failed to import row: {e}")
                        
        except Exception as e:
            print(f"Import error: {e}")
            
        return count

    def get_last_invoice_number(self):
        """Get the last generated invoice number"""
        conn = self._connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT invoice_number FROM invoices ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception:
            return None
        finally:
            conn.close()
