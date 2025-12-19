"""
Migration script for license history CSV
Updates the schema to include 'City' and match current configuration.
"""
import csv
import os
import shutil

# Define paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(SCRIPT_DIR, "license_history.csv")
BACKUP_FILE = os.path.join(SCRIPT_DIR, "license_history.bak")

# New headers as per config.py
NEW_HEADERS = [
    'Generated Date',
    'Customer Name',
    'Email',
    'Phone',
    'City',
    'Country',
    'HWID',
    'Expiry Date',
    'License Key',
    'License Type',
    'Invoice Number',
    'Amount',
    'Payment Method',
    'Payment Status',
    'Renewal Reminder',
    'Notes'
]

def migrate():
    if not os.path.exists(HISTORY_FILE):
        print("No history file found. Nothing to migrate.")
        return

    print(f"Reading {HISTORY_FILE}...")
    
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            old_headers = next(reader)
        except StopIteration:
            print("Empty file.")
            return
        
        rows = list(reader)

    print(f"Old headers: {old_headers}")
    
    # Check if migration is needed
    if old_headers == NEW_HEADERS:
        print("Headers already match. No migration needed.")
        return

    # Create backup
    shutil.copy2(HISTORY_FILE, BACKUP_FILE)
    print(f"Backup created at {BACKUP_FILE}")

    migrated_rows = []
    
    for row in rows:
        # Create a dictionary of old data
        row_dict = {}
        for i, header in enumerate(old_headers):
            if i < len(row):
                row_dict[header] = row[i]
        
        # Create new row based on NEW_HEADERS
        new_row = []
        for header in NEW_HEADERS:
            if header in row_dict:
                new_row.append(row_dict[header])
            elif header == 'City':
                # Try to map 'Address' to 'City' if it exists, otherwise empty
                new_row.append(row_dict.get('Address', ''))
            elif header == 'Address':
                 # Address is being removed, so we skip/ignore (not in NEW_HEADERS)
                 pass
            elif header == 'Support Tier':
                 # Support Tier removed
                 pass
            else:
                new_row.append('') # Empty for new fields
        
        migrated_rows.append(new_row)

    # Write new file
    with open(HISTORY_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(NEW_HEADERS)
        writer.writerows(migrated_rows)

    print("Migration complete!")
    print(f"Updated {len(migrated_rows)} rows.")

if __name__ == "__main__":
    migrate()
