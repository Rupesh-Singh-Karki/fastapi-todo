from fastapi import APIRouter, Depends
from src.auth.services.auth import register_user_service, login_user_service
from src.auth.schema import RegisterUser, LoginUser
from src.auth.services.dependencies import get_current_user  # NEW
from src.utils.jwt import decode_token, revoke_jti  # NEW
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # NEW
from src.utils.rate_limiter import rate_limiter  # NEW

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}}
)

@router.post("/register", dependencies=[Depends(rate_limiter("register", limit=3, period=3600))])  # NEW: Rate limiting
def register(user: RegisterUser):
    """
    Register a new user.
    """
    return register_user_service(user)

@router.post("/login", dependencies=[Depends(rate_limiter("login", limit=10, period=60))])  # NEW: Rate limiting
def login(user: LoginUser):
    """
    Login an existing user.
    """
    return login_user_service(user)

# NEW: Logout endpoint
@router.post("/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout by revoking the current token.
    """
    token = credentials.credentials
    payload = decode_token(token)
    jti = payload.get("jti")
    exp = payload.get("exp")
    
    # Revoke the token
    revoke_jti(jti, exp)
    
    return {"msg": "Logged out successfully"}