import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://127.0.0.1:8000/fineract-provider/api/v1"
AUTH = HTTPBasicAuth("mifos", "password")

def run_scenario():
    print("[SCENARIO] Transferring Funds (Checking -> Savings)...")
    
    payload = {
        "fromOfficeId": 1,
        "fromClientId": 1,
        "fromAccountType": 2,
        "fromAccountId": 1,
        "toOfficeId": 1,
        "toClientId": 1,
        "toAccountType": 2,
        "toAccountId": 2,
        "transferDate": "2026-06-16",
        "transferAmount": 150.00,
        "transferDescription": "Scenario transfer fund execution",
        "locale": "en",
        "dateFormat": "yyyy-MM-dd"
    }
    
    headers = {
        "Fineract-Platform-TenantId": "default",
        "Content-Type": "application/json"
    }
    
    resp = requests.post(f"{BASE_URL}/accounttransfers", json=payload, headers=headers, auth=AUTH)
    if resp.status_code == 200 or resp.status_code == 201:
        data = resp.json()
        print(f"[SUCCESS] Fund transfer completed successfully!")
        print(f"Transaction Resource ID: {data.get('resourceId')}")
    else:
        print(f"[FAILED] Transfer failed: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    run_scenario()
