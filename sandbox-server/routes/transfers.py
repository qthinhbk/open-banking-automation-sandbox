import json
import time
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/transfers", tags=["Transfers"])
security = HTTPBearer()

SECRET_KEY = "super_secret_sandbox_key"
ALGORITHM = "HS256"
DB_PATH = "d:/open-banking-automation-sandbox/sandbox-server/mock-data/db.json"

class TransferRequest(BaseModel):
    source_account: str
    destination_account: str
    amount: float
    description: str

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        token = credentials.credentials
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if decoded.get("type") != "access_token":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        return decoded.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def load_db() -> Dict[str, Any]:
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_db(db: Dict[str, Any]):
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2)

@router.post("/initiate")
def initiate_transfer(payload: TransferRequest, username: str = Depends(get_current_user)):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Transfer amount must be greater than zero")
        
    db = load_db()
    user_data = db.get("users", {}).get(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User data not found")
        
    # Find source account and check balance
    source_acc = None
    for acc in user_data.get("accounts", []):
        if acc["account_number"] == payload.source_account:
            source_acc = acc
            break
            
    if not source_acc:
        raise HTTPException(status_code=400, detail="Source account not found or access denied")
        
    if source_acc["balance"] < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
        
    # Deduct balance
    source_acc["balance"] -= payload.amount
    
    # Append new transaction
    tx_id = f"tx_{int(time.time() * 1000)}"
    new_tx = {
        "id": tx_id,
        "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "description": payload.description,
        "amount": -payload.amount,
        "type": "DEBIT",
        "account_number": payload.source_account
    }
    user_data["transactions"].append(new_tx)
    
    save_db(db)
    
    return {
        "status": "SUCCESS",
        "transaction_id": tx_id,
        "message": f"Successfully transferred {payload.amount} USD to account {payload.destination_account}"
    }
