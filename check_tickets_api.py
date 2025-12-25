import requests
import json

BASE_URL = "http://localhost:8000/api"

def check_tickets():
    try:
        # Simulate Staff user
        headers = {
            "X-User-ID": "1",
            "X-User-Role": "staff"
        }
        
        # Call get_tickets (include_returned=true)
        resp = requests.get(f"{BASE_URL}/tickets/?include_returned=true", headers=headers)
        
        if resp.status_code != 200:
            print(f"❌ API Failed: {resp.status_code}")
            print(resp.text)
            return

        tickets = resp.json()
        print(f"✅ API returned {len(tickets)} tickets")
        
        active = [t for t in tickets if t['status'].lower() not in ['completed', 'cancelled'] and t['device_status'] != 'returned']
        completed = [t for t in tickets if t['status'].lower() in ['completed', 'cancelled']]
        
        print(f" - Active: {len(active)}")
        print(f" - Completed: {len(completed)}")
        
        if len(tickets) > 0:
            print("Sample active ticket:", active[0] if active else "None")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_tickets()
