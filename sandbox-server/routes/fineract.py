import json
import time
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter(prefix="/fineract-provider/api/v1", tags=["Apache Fineract Compatibility"])
security = HTTPBasic()

DB_PATH = "d:/open-banking-automation-sandbox/sandbox-server/mock-data/db.json"

class FineractTransferRequest(BaseModel):
    fromOfficeId: int
    fromClientId: int
    fromAccountType: int
    fromAccountId: int
    toOfficeId: int
    toClientId: int
    toAccountType: int
    toAccountId: int
    transferDate: str
    transferAmount: float
    transferDescription: str
    locale: str
    dateFormat: str

def authenticate_fineract(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    # Fineract traditionally uses Basic Authentication (e.g. mifos/password or mifos/mifos)
    if credentials.username == "mifos" and credentials.password == "password":
        return "demo_user"
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Fineract credentials",
        headers={"WWW-Authenticate": "Basic"},
    )

def load_db() -> Dict[str, Any]:
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_db(db: Dict[str, Any]):
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2)

@router.get("/savingsaccounts/{accountId}")
def get_fineract_savings_account(
    accountId: int, 
    associations: Optional[str] = Query(None), 
    username: str = Depends(authenticate_fineract)
):
    db = load_db()
    user_data = db.get("users", {}).get(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Map index or ID to our mock account numbers
    # For simulation, accountId 1 maps to checking (index 0), accountId 2 maps to savings (index 1)
    accounts = user_data.get("accounts", [])
    if accountId == 1 and len(accounts) > 0:
        acc = accounts[0]
    elif accountId == 2 and len(accounts) > 1:
        acc = accounts[1]
    else:
        raise HTTPException(status_code=404, detail="Savings account not found in Fineract ledger")

    # Construct Apache Fineract standard SavingsAccountData JSON response
    response_data = {
        "id": accountId,
        "accountNo": acc["account_number"],
        "clientId": 1,
        "clientName": "Demo User",
        "savingsProductId": 1,
        "savingsProductName": "Regular Savings",
        "fieldOfficerId": 0,
        "status": {
            "id": 300,
            "code": "savingsAccountStatusType.active",
            "description": "Active"
        },
        "timeline": {
            "submittedOnDate": [2026, 6, 15],
            "submittedByUsername": "mifos",
            "activatedOnDate": [2026, 6, 15],
            "activatedByUsername": "mifos"
        },
        "currency": {
            "code": acc["currency"],
            "name": "US Dollar" if acc["currency"] == "USD" else "Local Currency",
            "decimalPlaces": 2,
            "displaySymbol": "$"
        },
        "summary": {
            "accountBalance": acc["balance"]
        }
    }

    # If transactions are requested (as in AccountTransfersApiResource.java or mobile dashboards)
    if associations and "transactions" in associations:
        fineract_txs = []
        for idx, tx in enumerate(user_data.get("transactions", [])):
            if tx["account_number"] == acc["account_number"]:
                fineract_txs.append({
                    "id": idx + 1,
                    "transactionType": {
                        "id": 1 if tx["amount"] > 0 else 2,
                        "code": "savingsAccountTransactionType.deposit" if tx["amount"] > 0 else "savingsAccountTransactionType.withdrawal",
                        "description": "Deposit" if tx["amount"] > 0 else "Withdrawal"
                    },
                    "date": [2026, 6, 15],  # Standard Fineract integer date array [yyyy, MM, dd]
                    "currency": {
                        "code": "USD",
                        "displaySymbol": "$"
                    },
                    "amount": abs(tx["amount"]),
                    "runningBalance": acc["balance"],  # simplified
                    "reversed": False
                })
        response_data["transactions"] = fineract_txs

    return response_data

@router.post("/accounttransfers")
def post_fineract_transfer(
    payload: FineractTransferRequest, 
    username: str = Depends(authenticate_fineract)
):
    db = load_db()
    user_data = db.get("users", {}).get(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    accounts = user_data.get("accounts", [])
    
    # Map fromAccountId and toAccountId to mock accounts
    src_acc = None
    dest_acc = None
    
    if payload.fromAccountId == 1 and len(accounts) > 0:
        src_acc = accounts[0]
    elif payload.fromAccountId == 2 and len(accounts) > 1:
        src_acc = accounts[1]
        
    if payload.toAccountId == 1 and len(accounts) > 0:
        dest_acc = accounts[0]
    elif payload.toAccountId == 2 and len(accounts) > 1:
        dest_acc = accounts[1]

    if not src_acc or not dest_acc:
        raise HTTPException(status_code=404, detail="Source or destination account not found")

    if src_acc["balance"] < payload.transferAmount:
        raise HTTPException(status_code=400, detail="Insufficient funds for Fineract transfer")

    # Process transfer
    src_acc["balance"] -= payload.transferAmount
    dest_acc["balance"] += payload.transferAmount

    # Append transaction logs
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    tx_id_src = f"tx_{int(time.time() * 1000)}_src"
    tx_id_dest = f"tx_{int(time.time() * 1000)}_dest"

    user_data["transactions"].append({
        "id": tx_id_src,
        "date": timestamp,
        "description": f"Transfer to Acc {dest_acc['account_number']}: {payload.transferDescription}",
        "amount": -payload.transferAmount,
        "type": "DEBIT",
        "account_number": src_acc["account_number"]
    })

    user_data["transactions"].append({
        "id": tx_id_dest,
        "date": timestamp,
        "description": f"Transfer from Acc {src_acc['account_number']}: {payload.transferDescription}",
        "amount": payload.transferAmount,
        "type": "CREDIT",
        "account_number": dest_acc["account_number"]
    })

    save_db(db)

    # Return standard Fineract CommandProcessingResult response structure
    return {
        "officeId": payload.fromOfficeId,
        "clientId": payload.fromClientId,
        "savingsId": payload.fromAccountId,
        "resourceId": int(time.time() * 1000) % 100000,
        "changes": {
            "transferDescription": payload.transferDescription,
            "transferAmount": payload.transferAmount
        }
    }

@router.post("/clients")
def post_fineract_client(payload: Dict[str, Any], username: str = Depends(authenticate_fineract)):
    # Simulates creating a new client
    return {
        "officeId": payload.get("officeId", 1),
        "clientId": 1,
        "resourceId": 101,
        "changes": {
            "firstname": payload.get("firstname"),
            "lastname": payload.get("lastname")
        }
    }

@router.post("/savingsaccounts")
def post_fineract_savings(payload: Dict[str, Any], username: str = Depends(authenticate_fineract)):
    # Simulates creating a new savings account application
    return {
        "officeId": payload.get("officeId", 1),
        "clientId": payload.get("clientId", 1),
        "savingsId": 1,
        "resourceId": 202
    }

