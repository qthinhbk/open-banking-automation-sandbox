import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://127.0.0.1:8000/fineract-provider/api/v1"
AUTH = HTTPBasicAuth("mifos", "password")

def run_scenario():
    print("[SCENARIO] Opening Savings Account Application...")
    
    payload = {
        "clientId": 1,
        "productId": 1,
        "submittedOnDate": "2026-06-16",
        "dateFormat": "yyyy-MM-dd",
        "locale": "en"
    }
    
    headers = {
        "Fineract-Platform-TenantId": "default",
        "Content-Type": "application/json"
    }
    
    resp = requests.post(f"{BASE_URL}/savingsaccounts", json=payload, headers=headers, auth=AUTH)
    if resp.status_code == 200 or resp.status_code == 201:
        data = resp.json()
        print(f"[SUCCESS] Savings account application submitted successfully!")
        print(f"Savings ID: {data.get('savingsId')}")
        print(f"Resource ID: {data.get('resourceId')}")
    else:
        print(f"[FAILED] Failed to open savings: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    run_scenario()
