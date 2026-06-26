import time
import jwt
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

SECRET_KEY = "super_secret_sandbox_key"
ALGORITHM = "HS256"

# In-memory storage for active OTPs for demonstration purposes
# format: { username: { "otp": str, "expires_at": float } }
active_otps = {}

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    message: str
    requires_otp: bool
    otp_token: Optional[str] = None

class OtpRequest(BaseModel):
    username: str
    otp_token: str
    otp_code: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    # For simulation, username demo_user and password password123 are accepted
    if payload.username == "demo_user" and payload.password == "password123":
        # Generate a temporary OTP token
        otp_token = jwt.encode({"sub": payload.username, "type": "otp_challenge", "exp": time.time() + 300}, SECRET_KEY, algorithm=ALGORITHM)
        # Mock OTP code generated (always 123456 for easy local sandbox demo)
        active_otps[payload.username] = {
            "code": "123456",
            "expires_at": time.time() + 300
        }
        return {
            "message": "Credentials verified. OTP authentication required.",
            "requires_otp": True,
            "otp_token": otp_token
        }
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password"
    )

@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(payload: OtpRequest):
    try:
        decoded = jwt.decode(payload.otp_token, SECRET_KEY, algorithms=[ALGORITHM])
        if decoded.get("sub") != payload.username or decoded.get("type") != "otp_challenge":
            raise HTTPException(status_code=400, detail="Invalid OTP token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Expired or invalid OTP token")

    otp_info = active_otps.get(payload.username)
    if not otp_info or otp_info["expires_at"] < time.time():
        raise HTTPException(status_code=400, detail="OTP expired or not requested")

    if otp_info["code"] != payload.otp_code:
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    # Clear OTP after use
    active_otps.pop(payload.username, None)

    # Generate final bearer token
    access_token = jwt.encode({"sub": payload.username, "type": "access_token", "exp": time.time() + 3600}, SECRET_KEY, algorithm=ALGORITHM)
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
