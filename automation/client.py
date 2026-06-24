import requests
from requests.auth import HTTPBasicAuth

class FineractClient:
    def __init__(self, base_url="http://127.0.0.1:8080/fineract-provider/api/v1", username="mifos", password="password", tenant="default"):
        self.base_url = base_url
        self.auth = HTTPBasicAuth(username, password)
        self.headers = {
            "Fineract-Platform-TenantId": tenant,
            "Content-Type": "application/json"
        }

    def create_client(self, firstname, lastname, office_id=1):
        payload = {
            "firstname": firstname,
            "lastname": lastname,
            "officeId": office_id,
            "active": True,
            "activationDate": "2026-06-16",
            "dateFormat": "yyyy-MM-dd",
            "locale": "en",
            "legalFormId": 1
        }
        resp = requests.post(f"{self.base_url}/clients", json=payload, headers=self.headers, auth=self.auth)
        return resp.json() if resp.status_code in [200, 201] else resp.raise_for_status()

    def open_savings_account(self, client_id, product_id=1):
        payload = {
            "clientId": client_id,
            "productId": product_id,
            "submittedOnDate": "2026-06-16",
            "dateFormat": "yyyy-MM-dd",
            "locale": "en"
        }
        resp = requests.post(f"{self.base_url}/savingsaccounts", json=payload, headers=self.headers, auth=self.auth)
        return resp.json() if resp.status_code in [200, 201] else resp.raise_for_status()

    def transfer_funds(self, from_id, to_id, amount, description="Fund Transfer"):
        payload = {
            "fromOfficeId": 1,
            "fromClientId": 1,
            "fromAccountType": 2,
            "fromAccountId": from_id,
            "toOfficeId": 1,
            "toClientId": 1,
            "toAccountType": 2,
            "toAccountId": to_id,
            "transferDate": "2026-06-16",
            "transferAmount": amount,
            "transferDescription": description,
            "locale": "en",
            "dateFormat": "yyyy-MM-dd"
        }
        resp = requests.post(f"{self.base_url}/accounttransfers", json=payload, headers=self.headers, auth=self.auth)
        return resp.json() if resp.status_code in [200, 201] else resp.raise_for_status()

    def get_savings_account(self, account_id, associations=None):
        params = {}
        if associations:
            params["associations"] = associations
        resp = requests.get(f"{self.base_url}/savingsaccounts/{account_id}", params=params, headers=self.headers, auth=self.auth)
        return resp.json() if resp.status_code == 200 else resp.raise_for_status()

if __name__ == "__main__":
    client = FineractClient()
    print("Testing client class...")
    try:
        res = client.create_client("John", "Doe")
        print(f"Created: ID {res.get('clientId')}")
    except Exception as e:
        print(f"Test run failed (expected if Fineract is not running): {e}")
