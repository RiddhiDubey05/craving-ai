from fastapi import APIRouter, HTTPException, Header, Depends, status
from pydantic import BaseModel
from typing import Optional, List

from backend.db.db_manager import db_manager
from backend.utils.logger import app_logger
from backend.services.email_service import send_otp_email

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class SendOTPRequest(BaseModel):
    phone_or_email: str

class VerifyOTPRequest(BaseModel):
    phone_or_email: str
    code: str

class ProfileSetupRequest(BaseModel):
    name: str
    avatar_id: str
    preferences: List[str]

class AuthResponse(BaseModel):
    token: str
    is_new_user: bool

# Helper dependency to resolve user from authorization header
def get_current_user_id(authorization: Optional[str] = Header(None)) -> Optional[int]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    return db_manager.verify_session(token)

def require_user_id(user_id: Optional[int] = Depends(get_current_user_id)) -> int:
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user_id

@router.post("/send-otp")
async def send_otp(req: SendOTPRequest):
    phone_or_email = req.phone_or_email.strip().lower()
    if len(phone_or_email) < 5:
        raise HTTPException(status_code=400, detail="Invalid email or phone number.")
        
    try:
        code = db_manager.create_otp(phone_or_email)
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))
    
    # Real Email Delivery via Resend
    success = send_otp_email(phone_or_email, code)
    if not success:
        app_logger.error(
            f"Failed to send OTP email to {phone_or_email}. "
            "Check RESEND_API_KEY in .env and backend logs."
        )
        raise HTTPException(
            status_code=503,
            detail=(
                "Email delivery failed. "
                "Please check your email address and try again. "
                "If this persists, contact support."
            )
        )
    
    app_logger.info(f"OTP email dispatched successfully to {phone_or_email}")
    return {"message": f"OTP sent to {phone_or_email}"}


@router.post("/verify-otp", response_model=AuthResponse)
async def verify_otp(req: VerifyOTPRequest):
    phone_or_email = req.phone_or_email.strip().lower()
    
    is_valid = db_manager.verify_otp(phone_or_email, req.code)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP.")
        
    user_info = db_manager.get_or_create_user(phone_or_email)
    token = db_manager.create_session(user_info["id"])
    
    return AuthResponse(token=token, is_new_user=not user_info["verified"])


@router.post("/setup-profile")
async def setup_profile(req: ProfileSetupRequest, user_id: int = Depends(require_user_id)):
    if len(req.name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Name must be at least 2 characters.")
        
    db_manager.create_user_profile(user_id, req.name.strip(), req.avatar_id, req.preferences)
    return {"message": "Profile setup complete"}


@router.get("/me")
async def get_me(user_id: int = Depends(require_user_id)):
    profile = db_manager.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile


@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        db_manager.delete_session(token)
    return {"message": "Logged out successfully"}


@router.get("/test-email")
async def test_email(to: str):
    """
    Diagnostic endpoint: send a test OTP email to verify Resend is configured.
    Usage: GET /api/auth/test-email?to=yourname@gmail.com
    """
    success = send_otp_email(to, "123456")
    if success:
        return {"status": "ok", "message": f"Test email sent to {to}. Check your inbox!"}
    raise HTTPException(
        status_code=503,
        detail="Email failed. Check RESEND_API_KEY in .env and server logs for details."
    )
