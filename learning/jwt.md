
# `src/utils/jwt.py` — Beginner Explanation (Line-by-line)

This file implements JWT creation and decoding used for authentication. The code below is followed by detailed explanations for each line.

---

Code (complete file):

```python
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
```

Line-by-line explanation:

1. `from src.config import settings`
  - Access to app configuration such as `JWT_SECRET_KEY` and expiry minutes from `.env`.

2. `from datetime import datetime, timedelta`
  - Datetime utilities for issuing and expiring tokens.

3. `from typing import Dict, Any`
  - Type hints used in function signatures for clarity.

4. `import jwt`
  - The `pyjwt` library for encoding and decoding JWT tokens.

5-7. `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
  - Load token config from `settings`. `ACCESS_TOKEN_EXPIRE_MINUTES` controls token lifetime.

8. `BLACKLIST = set()`
  - A simple in-memory set used to store revoked token identifiers (JTIs). Not persistent across restarts.

9-13. `_make_jti()`
  - Generates a unique token identifier using `uuid.uuid4()`.

14-29. `create_access_token(identity: str)`
  - `now = datetime.utcnow()` — use UTC for consistency.
  - `exp = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)` — calculate expiration.
  - `payload = {"sub": ..., "iat": ..., "exp": ..., "jti": ...}` — define JWT claims.
  - `token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)` — sign and return the token.

30-38. `decode_token(token: str)`
  - Use `jwt.decode` to verify signature and check the `exp` claim automatically.
  - If the JTI is in `BLACKLIST` raise `InvalidTokenError`.

39-40. `revoke_jti(jti: str)`
  - Adds a token id to the blacklist.

Security notes for beginners:
- Blacklisting in memory is okay for testing but not for production. Use Redis or a DB for persistent blacklists.
- Keep `JWT_SECRET_KEY` secret and rotate if compromised.

---
