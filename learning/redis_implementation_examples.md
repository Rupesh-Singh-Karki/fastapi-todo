# Redis Implementation Examples

This file shows **before and after** code examples for adding Redis to your existing project.

---

## Example 1: Cache User Data in Authentication

### ❌ Before (Without Redis)

**File:** `/src/auth/services/dependencies.py`

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.utils.jwt import decode_token
from src.utils.db import user_collection
from bson import ObjectId
import jwt

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = decode_token(token)
        user_id = payload.get("sub")
        
        # Always queries database - SLOW! 🐌
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
```

### ✅ After (With Redis Cache)

**File:** `/src/auth/services/dependencies.py`

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.utils.jwt import decode_token
from src.utils.db import user_collection
from src.utils.redis_client import get_cache, set_cache  # NEW
from bson import ObjectId
import jwt

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = decode_token(token)
        user_id = payload.get("sub")
        
        # NEW: Try cache first - FAST! ⚡
        cache_key = f"user:{user_id}"
        cached_user = get_cache(cache_key)
        
        if cached_user:
            # Convert _id back to ObjectId for consistency
            cached_user["_id"] = ObjectId(cached_user["_id"])
            return cached_user
        
        # If not cached, fetch from database
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        # NEW: Cache the user for 10 minutes (600 seconds)
        user_to_cache = {
            "_id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"]
        }
        set_cache(cache_key, user_to_cache, expire=600)
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
```

**What changed:**
- ✅ Added Redis cache check before database query
- ✅ Cache hit = instant response (no database query)
- ✅ Cache miss = query database + cache for next time
- ✅ Cache expires after 10 minutes automatically

---

## Example 2: Cache Todo Lists

### ❌ Before (Without Redis)

**File:** `/src/todo/services/todo.py`

```python
def get_all_todos_service(user_id: str):
    # Always queries database - SLOW for repeated requests! 🐌
    todos = list(todo_collection.find({"user_id": ObjectId(user_id)}))
    result = []
    for t in todos:
        result.append({
            "id": str(t["_id"]),
            "heading": t["heading"],
            "task": t["task"],
            "completed": t["completed"],
            "created_at": t["created_at"].isoformat() if isinstance(t["created_at"], datetime) else t["created_at"],
            "updated_at": t["updated_at"].isoformat() if isinstance(t["updated_at"], datetime) else t["updated_at"],
            "completion_time": t["completion_time"].isoformat() if t.get("completion_time") else None,
            "reminder_sent": t.get("reminder_sent", False)
        })
    return result
```

### ✅ After (With Redis Cache)

**File:** `/src/todo/services/todo.py`

```python
from src.utils.redis_client import get_cache, set_cache, delete_cache  # NEW

def get_all_todos_service(user_id: str):
    # NEW: Try cache first - FAST! ⚡
    cache_key = f"todos:{user_id}"
    cached_todos = get_cache(cache_key)
    
    if cached_todos:
        return cached_todos
    
    # If not cached, query database
    todos = list(todo_collection.find({"user_id": ObjectId(user_id)}))
    result = []
    for t in todos:
        result.append({
            "id": str(t["_id"]),
            "heading": t["heading"],
            "task": t["task"],
            "completed": t["completed"],
            "created_at": t["created_at"].isoformat() if isinstance(t["created_at"], datetime) else t["created_at"],
            "updated_at": t["updated_at"].isoformat() if isinstance(t["updated_at"], datetime) else t["updated_at"],
            "completion_time": t["completion_time"].isoformat() if t.get("completion_time") else None,
            "reminder_sent": t.get("reminder_sent", False)
        })
    
    # NEW: Cache for 5 minutes (300 seconds)
    set_cache(cache_key, result, expire=300)
    
    return result
```

**What changed:**
- ✅ Cache check before database query
- ✅ Repeated requests return cached data instantly
- ✅ Cache expires after 5 minutes

---

## Example 3: Invalidate Cache on Updates

### ❌ Before (Without Redis)

**File:** `/src/todo/services/todo.py`

```python
def create_todo_service(user_id: str, heading: str, task: str, completion_time: Optional[datetime] = None):
    now = datetime.utcnow()
    new_todo = {
        "user_id": ObjectId(user_id),
        "heading": heading,
        "task": task,
        "completed": False,
        "created_at": now,
        "updated_at": now,
        "completion_time": completion_time,
        "reminder_sent": False
    }
    result = todo_collection.insert_one(new_todo)
    new_todo["_id"] = result.inserted_id
    # User's todo list is now outdated in cache! ❌
    return {
        "id": str(new_todo["_id"]),
        "heading": new_todo["heading"],
        "task": new_todo["task"],
        "completed": new_todo["completed"],
        "created_at": new_todo["created_at"].isoformat(),
        "updated_at": new_todo["updated_at"].isoformat(),
        "completion_time": new_todo["completion_time"].isoformat() if new_todo["completion_time"] else None,
        "reminder_sent": new_todo["reminder_sent"]
    }
```

### ✅ After (With Cache Invalidation)

**File:** `/src/todo/services/todo.py`

```python
from src.utils.redis_client import delete_cache  # NEW

def create_todo_service(user_id: str, heading: str, task: str, completion_time: Optional[datetime] = None):
    now = datetime.utcnow()
    new_todo = {
        "user_id": ObjectId(user_id),
        "heading": heading,
        "task": task,
        "completed": False,
        "created_at": now,
        "updated_at": now,
        "completion_time": completion_time,
        "reminder_sent": False
    }
    result = todo_collection.insert_one(new_todo)
    new_todo["_id"] = result.inserted_id
    
    # NEW: Invalidate the user's todo list cache
    delete_cache(f"todos:{user_id}")
    
    return {
        "id": str(new_todo["_id"]),
        "heading": new_todo["heading"],
        "task": new_todo["task"],
        "completed": new_todo["completed"],
        "created_at": new_todo["created_at"].isoformat(),
        "updated_at": new_todo["updated_at"].isoformat(),
        "completion_time": new_todo["completion_time"].isoformat() if new_todo["completion_time"] else None,
        "reminder_sent": new_todo["reminder_sent"]
    }
```

**Apply same pattern to update and delete:**

```python
def update_todo_service(user_id: str, todo_id: str, data: dict):
    # ... your existing update code ...
    
    # NEW: Invalidate caches
    delete_cache(f"todos:{user_id}")
    delete_cache(f"todo:{todo_id}")
    
    return {"msg": "Todo updated successfully"}


def delete_todo_service(user_id: str, todo_id: str):
    # ... your existing delete code ...
    
    # NEW: Invalidate caches
    delete_cache(f"todos:{user_id}")
    delete_cache(f"todo:{todo_id}")
    
    return {"msg": "Todo deleted successfully"}
```

**What changed:**
- ✅ Cache is cleared when data changes
- ✅ Next request will fetch fresh data from database
- ✅ Fresh data gets cached again

---

## Example 4: Add Logout Functionality

### Problem: Currently no way to revoke JWT tokens

Users cannot truly "logout" because JWTs are stateless. If someone steals a token, it remains valid until expiration.

### Solution: JWT Token Blacklist with Redis

**Step 1: Update `/src/utils/jwt.py`**

```python
from src.utils.redis_client import is_token_blacklisted, blacklist_token  # NEW
import uuid

def create_access_token(identity: str) -> str:
    now = datetime.utcnow()
    exp = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    jti = str(uuid.uuid4())  # NEW: Add unique token ID
    
    payload = {
        "sub": str(identity),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": jti,  # NEW
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_token(token: str) -> Dict[str, Any]:
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    jti = payload.get("jti")
    
    # NEW: Check if token is blacklisted
    if is_token_blacklisted(jti):
        raise jwt.InvalidTokenError("Token revoked")
    
    return payload
```

**Step 2: Add Logout Endpoint in `/src/auth/routes/auth.py`**

```python
from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.utils.jwt import decode_token
from src.utils.redis_client import blacklist_token

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

# ... existing register and login routes ...

# NEW: Logout endpoint
@router.post("/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout by revoking the current token.
    Token will be blacklisted until its natural expiration.
    """
    token = credentials.credentials
    payload = decode_token(token)
    jti = payload.get("jti")
    exp = payload.get("exp")
    
    # Blacklist the token
    blacklist_token(jti, exp)
    
    return {"msg": "Logged out successfully"}
```

**How to use:**

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Response: {"access_token": "eyJ..."}

# Use token for requests
curl http://localhost:8000/todo/ \
  -H "Authorization: Bearer eyJ..."

# Logout
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer eyJ..."

# Try to use same token again - will fail with "Token revoked"
curl http://localhost:8000/todo/ \
  -H "Authorization: Bearer eyJ..."
# Response: {"detail": "Token revoked"}
```

---

## Example 5: Add Rate Limiting

Prevent abuse by limiting requests per user/IP.

**Create `/src/utils/rate_limiter.py`:**

```python
from fastapi import Request, HTTPException, status
from src.utils.redis_client import check_rate_limit


def rate_limit(key_prefix: str, max_requests: int = 10, window: int = 60):
    """
    Rate limiting dependency.
    
    Args:
        key_prefix: Prefix for rate limit key (e.g., "login", "register")
        max_requests: Maximum requests allowed in window
        window: Time window in seconds
    """
    async def check_rate(request: Request):
        # Use IP address as identifier
        client_ip = request.client.host
        key = f"rate_limit:{key_prefix}:{client_ip}"
        
        if not check_rate_limit(key, max_requests, window):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {max_requests} requests per {window} seconds."
            )
    
    return check_rate
```

**Use in routes `/src/auth/routes/auth.py`:**

```python
from fastapi import APIRouter, Depends
from src.utils.rate_limiter import rate_limit  # NEW

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Add rate limiting: max 5 login attempts per minute
@router.post("/login", dependencies=[Depends(rate_limit("login", max_requests=5, window=60))])
def login(user: LoginUser):
    return login_user_service(user)

# Add rate limiting: max 3 registrations per hour per IP
@router.post("/register", dependencies=[Depends(rate_limit("register", max_requests=3, window=3600))])
def register(user: RegisterUser):
    return register_user_service(user)
```

**What this does:**
- ✅ Prevents brute force login attacks
- ✅ Prevents mass registration spam
- ✅ Returns 429 error when limit exceeded
- ✅ Automatic reset after time window

---

## Performance Comparison

### Without Redis (Database Every Time):
```
Request 1: Database query (50ms)
Request 2: Database query (50ms)
Request 3: Database query (50ms)
Request 4: Database query (50ms)
Request 5: Database query (50ms)
Total: 250ms for 5 requests
```

### With Redis Cache:
```
Request 1: Database query + cache (50ms)
Request 2: Cache hit (1ms) ⚡
Request 3: Cache hit (1ms) ⚡
Request 4: Cache hit (1ms) ⚡
Request 5: Cache hit (1ms) ⚡
Total: 54ms for 5 requests (5x faster!)
```

---

## Summary: What to Add Where

| Feature | File | Function |
|---------|------|----------|
| Cache user data | `/src/auth/services/dependencies.py` | `get_current_user()` |
| Cache todo lists | `/src/todo/services/todo.py` | `get_all_todos_service()` |
| Invalidate on create | `/src/todo/services/todo.py` | `create_todo_service()` |
| Invalidate on update | `/src/todo/services/todo.py` | `update_todo_service()` |
| Invalidate on delete | `/src/todo/services/todo.py` | `delete_todo_service()` |
| JWT blacklist | `/src/utils/jwt.py` | `create_access_token()`, `decode_token()` |
| Logout endpoint | `/src/auth/routes/auth.py` | New `logout()` route |
| Rate limiting | `/src/utils/rate_limiter.py` | New file + apply to routes |

---

## Testing Your Implementation

After adding Redis caching:

```bash
# 1. Test cache hit
curl http://localhost:8000/todo/ -H "Authorization: Bearer YOUR_TOKEN"
# Check logs: should see "Cached: todos:USER_ID"

# 2. Make same request again
curl http://localhost:8000/todo/ -H "Authorization: Bearer YOUR_TOKEN"
# Should be MUCH faster (cache hit)

# 3. Create a new todo
curl -X POST http://localhost:8000/todo/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"heading":"Test","task":"Redis test"}'
# Check logs: should see "Deleted cache: todos:USER_ID"

# 4. Get todos again
curl http://localhost:8000/todo/ -H "Authorization: Bearer YOUR_TOKEN"
# Should query database (cache was invalidated)
# Check logs: should see new "Cached: todos:USER_ID"
```

---

**Ready to implement?**
1. Set up Redis Cloud (see `REDIS_SETUP.md`)
2. Run `python test_redis.py` to verify connection
3. Add caching code from examples above
4. Test and enjoy faster performance! ⚡
