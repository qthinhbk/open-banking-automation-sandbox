import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://127.0.0.1:8000/fineract-provider/api/v1"
AUTH = HTTPBasicAuth("mifos", "password")

def run_scenario():
    print("[SCENARIO] Initiating Client Onboarding...")
    
    payload = {
        "firstname": "Jane",
        "lastname": "Doe",
        "officeId": 1,
        "active": True,
        "activationDate": "2026-06-16",
        "dateFormat": "yyyy-MM-dd",
        "locale": "en",
        "legalFormId": 1
    }
    
    headers = {
        "Fineract-Platform-TenantId": "default",
        "Content-Type": "application/json"
    }
    
    resp = requests.post(f"{BASE_URL}/clients", json=payload, headers=headers, auth=AUTH)
    if resp.status_code == 200 or resp.status_code == 201:
        data = resp.json()
        print(f"[SUCCESS] Client onboarded successfully!")
        print(f"Client ID: {data.get('clientId')}")
        print(f"Resource ID: {data.get('resourceId')}")
    else:
        print(f"[FAILED] Onboarding failed: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    run_scenario()
