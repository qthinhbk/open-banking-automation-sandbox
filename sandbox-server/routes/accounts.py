import json
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from typing import List, Dict, Any

router = APIRouter(prefix="/api/v1/accounts", tags=["Accounts"])
security = HTTPBearer()

SECRET_KEY = "super_secret_sandbox_key"
ALGORITHM = "HS256"
DB_PATH = "d:/open-banking-automation-sandbox/sandbox-server/mock-data/db.json"

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

@router.get("/summary")
def get_summary(username: str = Depends(get_current_user)):
    db = load_db()
    user_data = db.get("users", {}).get(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User data not found")
    
    return {
        "accounts": user_data.get("accounts", [])
    }

@router.get("/transactions")
def get_transactions(account_number: str, username: str = Depends(get_current_user)):
    db = load_db()
    user_data = db.get("users", {}).get(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User data not found")
    
    # Verify account belongs to user
    has_account = any(acc["account_number"] == account_number for acc in user_data.get("accounts", []))
    if not has_account:
        raise HTTPException(status_code=403, detail="Access to account denied")
        
    transactions = [tx for tx in user_data.get("transactions", []) if tx["account_number"] == account_number]
    return {
        "account_number": account_number,
        "transactions": transactions
    }
