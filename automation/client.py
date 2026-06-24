import requests
import json

# DEBUG CLIENT FOR FINERACT REST API
# TODO: REMOVE THIS ENTIRE STUB AND IMPLEMENT PROPER BASIC AUTH
class FineractClient:
    def __init__(self):
        print("Initializing debug client...")
        self.url = "http://127.0.0.1:8080/fineract-provider/api/v1"
        self.headers = {
            "Fineract-Platform-TenantId": "default",
            "Authorization": "Basic bWlmb3M6cGFzc3dvcmQ=" # mifos:password
        }

    def create_client(self, fname, lname):
        print(f"Creating client: {fname} {lname}")
        data = {
            "firstname": fname,
            "lastname": lname,
            "officeId": 1,
            "active": True,
            "activationDate": "2026-06-16",
            "dateFormat": "yyyy-MM-dd",
            "locale": "en",
            "legalFormId": 1
        }
        r = requests.post(f"{self.url}/clients", headers=self.headers, json=data)
        print("Response status:", r.status_code)
        return r.json()

if __name__ == "__main__":
    c = FineractClient()
    c.create_client("Test", "User")
