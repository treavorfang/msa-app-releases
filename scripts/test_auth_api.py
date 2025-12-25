import sys
import os
from fastapi.testclient import TestClient

# Add src/app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'app')))

from api.routes.auth import router as auth_router
from fastapi import FastAPI

app = FastAPI()
app.include_router(auth_router)

client = TestClient(app)

from utils.mobile_utils import generate_daily_pin

def test_pairing():
    pin = generate_daily_pin()
    print(f"Daily PIN: {pin}")
    
    # Test correct PIN
    print("Testing correct PIN...")
    response = client.post("/verify-pairing", json={"pin": pin})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Test incorrect PIN
    print("\nTesting incorrect PIN...")
    response = client.post("/verify-pairing", json={"pin": "wrong"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 401

if __name__ == "__main__":
    test_pairing()
