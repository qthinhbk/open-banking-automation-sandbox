import requests
from requests.auth import HTTPBasicAuth
import sys

BASE_URL = "http://127.0.0.1:8080/fineract-provider/api/v1"
AUTH = HTTPBasicAuth("mifos", "password")
HEADERS = {
    "Fineract-Platform-TenantId": "default",
    "Content-Type": "application/json"
}

def check_response(resp, description):
    if resp.status_code in [200, 201]:
        print(f"OK: {description}")
        return resp.json()
    else:
        print(f"FAILED: {description} ({resp.status_code}): {resp.text}")
        sys.exit(1)

def run_seeding():
    print("Starting Fineract data seeding...")

    alice_payload = {
        "firstname": "Alice",
        "lastname": "Smith",
        "officeId": 1,
        "active": True,
        "activationDate": "16 June 2026",
        "dateFormat": "dd MMMM yyyy",
        "locale": "en",
        "legalFormId": 1
    }
    alice_data = check_response(
        requests.post(f"{BASE_URL}/clients", json=alice_payload, headers=HEADERS, auth=AUTH),
        "Create Client Alice"
    )
    alice_client_id = alice_data["clientId"]

    bob_payload = {
        "firstname": "Bob",
        "lastname": "Jones",
        "officeId": 1,
        "active": True,
        "activationDate": "16 June 2026",
        "dateFormat": "dd MMMM yyyy",
        "locale": "en",
        "legalFormId": 1
    }
    bob_data = check_response(
        requests.post(f"{BASE_URL}/clients", json=bob_payload, headers=HEADERS, auth=AUTH),
        "Create Client Bob"
    )
    bob_client_id = bob_data["clientId"]

    alice_savings_payload = {
        "clientId": alice_client_id,
        "productId": 1,
        "submittedOnDate": "16 June 2026",
        "dateFormat": "dd MMMM yyyy",
        "locale": "en"
    }
    alice_savings_data = check_response(
        requests.post(f"{BASE_URL}/savingsaccounts", json=alice_savings_payload, headers=HEADERS, auth=AUTH),
        "Submit Alice Savings Application"
    )
    alice_savings_id = alice_savings_data["savingsId"]

    check_response(
        requests.post(f"{BASE_URL}/savingsaccounts/{alice_savings_id}?command=approve", json={
            "approvedOnDate": "16 June 2026",
            "dateFormat": "dd MMMM yyyy",
            "locale": "en"
        }, headers=HEADERS, auth=AUTH),
        "Approve Alice Savings"
    )

    check_response(
        requests.post(f"{BASE_URL}/savingsaccounts/{alice_savings_id}?command=activate", json={
            "activatedOnDate": "16 June 2026",
            "dateFormat": "dd MMMM yyyy",
            "locale": "en"
        }, headers=HEADERS, auth=AUTH),
        "Activate Alice Savings"
    )

    bob_savings_payload = {
        "clientId": bob_client_id,
        "productId": 1,
        "submittedOnDate": "16 June 2026",
        "dateFormat": "dd MMMM yyyy",
        "locale": "en"
    }
    bob_savings_data = check_response(
        requests.post(f"{BASE_URL}/savingsaccounts", json=bob_savings_payload, headers=HEADERS, auth=AUTH),
        "Submit Bob Savings Application"
    )
    bob_savings_id = bob_savings_data["savingsId"]

    check_response(
        requests.post(f"{BASE_URL}/savingsaccounts/{bob_savings_id}?command=approve", json={
            "approvedOnDate": "16 June 2026",
            "dateFormat": "dd MMMM yyyy",
            "locale": "en"
        }, headers=HEADERS, auth=AUTH),
        "Approve Bob Savings"
    )

    check_response(
        requests.post(f"{BASE_URL}/savingsaccounts/{bob_savings_id}?command=activate", json={
            "activatedOnDate": "16 June 2026",
            "dateFormat": "dd MMMM yyyy",
            "locale": "en"
        }, headers=HEADERS, auth=AUTH),
        "Activate Bob Savings"
    )

    check_response(
        requests.post(f"{BASE_URL}/savingsaccounts/{alice_savings_id}/transactions?command=deposit", json={
            "locale": "en",
            "dateFormat": "dd MMMM yyyy",
            "transactionDate": "16 June 2026",
            "transactionAmount": 1000.00,
            "paymentTypeId": 1
        }, headers=HEADERS, auth=AUTH),
        "Deposit 1000.00 to Alice Savings"
    )

    check_response(
        requests.post(f"{BASE_URL}/savingsaccounts/{bob_savings_id}/transactions?command=deposit", json={
            "locale": "en",
            "dateFormat": "dd MMMM yyyy",
            "transactionDate": "16 June 2026",
            "transactionAmount": 500.00,
            "paymentTypeId": 1
        }, headers=HEADERS, auth=AUTH),
        "Deposit 500.00 to Bob Savings"
    )

    transfer_payload = {
        "fromOfficeId": 1,
        "fromClientId": alice_client_id,
        "fromAccountType": 2,
        "fromAccountId": alice_savings_id,
        "toOfficeId": 1,
        "toClientId": bob_client_id,
        "toAccountType": 2,
        "toAccountId": bob_savings_id,
        "transferDate": "16 June 2026",
        "transferAmount": 250.00,
        "transferDescription": "Alice to Bob sandbox transfer",
        "locale": "en",
        "dateFormat": "dd MMMM yyyy"
    }
    check_response(
        requests.post(f"{BASE_URL}/accounttransfers", json=transfer_payload, headers=HEADERS, auth=AUTH),
        "Transfer 250.00 from Alice to Bob"
    )

    check_response(
        requests.get(f"{BASE_URL}/savingsaccounts/{alice_savings_id}?associations=transactions", headers=HEADERS, auth=AUTH),
        "Query Alice transactions"
    )

    check_response(
        requests.get(f"{BASE_URL}/savingsaccounts/{bob_savings_id}?associations=transactions", headers=HEADERS, auth=AUTH),
        "Query Bob transactions"
    )

    print("Data seeding completed successfully.")

if __name__ == "__main__":
    run_seeding()
