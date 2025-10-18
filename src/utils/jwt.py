from src.config import settings
from datetime import datetime, timedelta
from typing import Dict, Any
import jwt


JWT_SECRET = settings.jwt_secret_key
JWT_ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_access_token_expire_minutes

BLACKLIST = set()


def _make_jti() -> str:
    import uuid

    return str(uuid.uuid4())


def create_access_token(identity: str) -> str:
    """
    Create a JWT with 'sub' and 'jti' claims and expiry.
    Returns a string token.
    """
    now = datetime.utcnow()
    exp = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    jti = _make_jti()
    payload = {
        "sub": str(identity),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": jti,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify token. Raises jwt exceptions on invalid/expired token.
    Also checks blacklist.
    """
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    jti = payload.get("jti")
    if jti in BLACKLIST:
        raise jwt.InvalidTokenError("Token revoked")
    return payload


def revoke_jti(jti: str) -> None:
    BLACKLIST.add(jti)