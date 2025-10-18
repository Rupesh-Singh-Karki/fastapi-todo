from fastapi import APIRouter
from src.auth.services.auth import register_user_service, login_user_service
from src.auth.schema import RegisterUser, LoginUser

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}}
)

@router.post("/register")
def register(user: RegisterUser):
    """
    Register a new user.
    """
    return register_user_service(user)

@router.post("/login")
def login(user: LoginUser):
    """
    Login an existing user.
    """
    return login_user_service(user)