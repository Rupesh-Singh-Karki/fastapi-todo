# How to Add Redis to Your Todo Project — Complete Guide

This guide explains step-by-step how to integrate Redis into your FastAPI Todo project. Redis is an in-memory data store that can be used for caching, session storage, rate limiting, and JWT token blacklisting.

---

## What is Redis and Why Use It?

**Redis** (Remote Dictionary Server) is an in-memory key-value store that's extremely fast. Common use cases:
- **Caching**: Store frequently accessed data (like user info, todos) to reduce database queries
- **Session storage**: Store user sessions
- **Token blacklist**: Store revoked JWT token IDs to prevent reuse
- **Rate limiting**: Track API request counts per user/IP
- **Pub/Sub**: Real-time messaging (advanced)

---

## Step 1: Set Up Cloud Redis (Recommended)

For production and easy setup, use a managed cloud Redis service. Here are the best options:

### Option A: Redis Cloud (Recommended - Free Tier Available) ⭐

**Why Redis Cloud:**
- ✅ Free tier: 30MB storage, perfect for learning
- ✅ No credit card required for free tier
- ✅ Automatic backups and monitoring
- ✅ Global availability
- ✅ Easy to upgrade when needed

**Setup Steps:**

1. **Sign up** at https://redis.com/try-free/
2. **Create a new database:**
   - Click "Create Database"
   - Choose "Fixed" plan (free tier)
   - Select region closest to you
   - Give it a name (e.g., "todo-app-cache")
   - Click "Create"
3. **Get connection details:**
   - After creation, click on your database
   - Copy the **Endpoint** (format: `redis-12345.c123.us-east-1-1.ec2.cloud.redislabs.com:12345`)
   - Copy the **Password** (default username is `default`)
4. **Connection URL format:**
   ```
   redis://default:YOUR_PASSWORD@YOUR_ENDPOINT
   ```
   Example:
   ```
   redis://default:abc123xyz@redis-12345.c123.us-east-1-1.ec2.cloud.redislabs.com:12345
   ```

### Option B: Upstash Redis (Serverless)

**Why Upstash:**
- ✅ True serverless (pay per request)
- ✅ Free tier: 10,000 requests/day
- ✅ REST API support
- ✅ Perfect for hobby projects

**Setup:** https://upstash.com/

### Option C: Railway.app

**Why Railway:**
- ✅ Simple deployment
- ✅ Free tier available
- ✅ One-click Redis deployment

**Setup:** https://railway.app/

### Option D: Render.com

**Why Render:**
- ✅ Free Redis instance (25MB)
- ✅ No credit card needed
- ✅ Simple setup

**Setup:** https://render.com/

---

### Local Redis (Development Only)

If you prefer local development:

**On Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install redis-server
sudo systemctl start redis
redis-cli ping  # Should return: PONG
```

**On macOS:**
```bash
brew install redis
brew services start redis
redis-cli ping
```

**Using Docker:**
```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

---

## Step 2: Install Python Redis Client

Add `redis` to your `requirements.txt`:

```txt
# existing packages...
redis==5.0.1
```

Install it:
```bash
pip install redis
```

---

## Step 3: Add Redis Configuration to `.env`

Update your `.env` file to include Redis connection settings.

**For Cloud Redis (Redis Cloud, Upstash, etc.):**

```env
# Existing settings
DB_URI=mongodb+srv://...
MONGO_DB=mydb
TODO_COLLECTION=todos
USER_COLLECTION=users
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email settings (you already have these)
EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
EMAIL_ENABLED=true

# NEW: Redis settings (Cloud Redis URL)
REDIS_URL=redis://default:YOUR_PASSWORD@YOUR_REDIS_ENDPOINT:PORT
# Example: redis://default:abc123xyz@redis-12345.c123.us-east-1-1.ec2.cloud.redislabs.com:12345
```

**For Local Redis (Development):**

```env
# Redis settings (Local)
REDIS_URL=redis://localhost:6379/0
```

**Important Notes:**
- Use `redis://` for non-SSL connections (local)
- Use `rediss://` for SSL connections (most cloud providers)
- Redis Cloud provides SSL by default, so use `rediss://`
- Format: `rediss://[username]:[password]@[host]:[port]`

---

## Step 4: Update `src/config.py`

Add Redis settings to your configuration:

```python
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH, env_file_encoding="utf-8", extra="ignore"
    )

    # Existing MongoDB settings
    db_uri: str = Field(..., env="DB_URI")
    root_path: str = Field("", env="ROOT_PATH")
    logging_level: str = Field("INFO", env="LOGGING_LEVEL")
    mongo_db: str = Field(..., env="MONGO_DB")
    todo_collection: str = Field(..., env="TODO_COLLECTION")
    user_collection: str = Field(..., env="USER_COLLECTION")
    
    # Existing JWT settings
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Email settings (you already have these)
    email_sender: str = Field(..., env="EMAIL_SENDER")
    email_password: str = Field(..., env="EMAIL_PASSWORD")
    smtp_host: str = Field("smtp.gmail.com", env="SMTP_HOST")
    smtp_port: int = Field(587, env="SMTP_PORT")
    email_enabled: bool = Field(True, env="EMAIL_ENABLED")
    
    # NEW: Redis settings (using connection URL for cloud Redis)
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")


settings = Settings()
```

---

## Step 5: Create Redis Client (`src/utils/redis_client.py`)

Create a new file to manage the Redis connection using the cloud Redis URL:

```python
import redis
from src.config import settings
from src.utils.logger import logger
import json

log = logger()

# Create Redis client using connection URL (works with cloud Redis)
redis_client = redis.from_url(
    settings.redis_url,
    decode_responses=True,  # Automatically decode bytes to strings
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True
)


def get_redis():
    """
    Get Redis client instance.
    """
    try:
        redis_client.ping()
        return redis_client
    except redis.ConnectionError:
        log.error("Failed to connect to Redis")
        return None


def set_cache(key: str, value: any, expire: int = 300):
    """
    Set a cache value in Redis with expiration (default 5 minutes).
    
    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        expire: Expiration time in seconds
    """
    try:
        redis_client.setex(key, expire, json.dumps(value))
        log.info(f"Cached: {key}")
    except Exception as e:
        log.error(f"Redis cache set error: {e}")


def get_cache(key: str):
    """
    Get a cached value from Redis.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None
    """
    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        log.error(f"Redis cache get error: {e}")
        return None


def delete_cache(key: str):
    """
    Delete a cache key from Redis.
    """
    try:
        redis_client.delete(key)
        log.info(f"Deleted cache: {key}")
    except Exception as e:
        log.error(f"Redis cache delete error: {e}")


def cache_exists(key: str) -> bool:
    """
    Check if a cache key exists.
    """
    try:
        return redis_client.exists(key) > 0
    except Exception as e:
        log.error(f"Redis exists check error: {e}")
        return False
```

---

## Step 6: Use Cases and Implementation Examples

### Use Case 1: Cache User Data

**Where:** `src/auth/services/dependencies.py`

**Why:** Reduce database queries for user lookups on every request.

**How to implement:**

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
        
        # NEW: Try to get user from cache first
        cache_key = f"user:{user_id}"
        cached_user = get_cache(cache_key)
        
        if cached_user:
            # Return cached user (convert _id back to ObjectId for consistency)
            cached_user["_id"] = ObjectId(cached_user["_id"])
            return cached_user
        
        # If not in cache, fetch from database
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
        )
```

**Important:** When a user updates their profile, invalidate the cache:
```python
from src.utils.redis_client import delete_cache

def update_user_profile(user_id: str, data: dict):
    # Update user in database
    result = user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": data})
    
    # Invalidate cache
    delete_cache(f"user:{user_id}")
    
    return {"msg": "Profile updated"}
```

---

### Use Case 2: Cache Todo Lists

**Where:** `src/todo/services/todo.py`

**Why:** Reduce database queries when fetching todos.

**How to implement:**

```python
from src.utils.redis_client import get_cache, set_cache, delete_cache

def get_all_todos_service(user_id: str):
    # Try cache first
    cache_key = f"todos:{user_id}"
    cached_todos = get_cache(cache_key)
    
    if cached_todos:
        return cached_todos
    
    # If not cached, fetch from database
    todos = list(todo_collection.find({"user_id": ObjectId(user_id)}))
    result = []
    for t in todos:
        result.append({
            "id": str(t["_id"]),
            "heading": t["heading"],
            "task": t["task"],
            "completed": t["completed"],
            "created_at": t["created_at"].isoformat() if isinstance(t["created_at"], datetime) else t["created_at"],
            "updated_at": t["updated_at"].isoformat() if isinstance(t["updated_at"], datetime) else t["updated_at"]
        })
    
    # Cache for 5 minutes
    set_cache(cache_key, result, expire=300)
    
    return result


def create_todo_service(user_id: str, heading: str, task: str):
    # ... existing create logic ...
    
    # Invalidate the user's todo list cache
    delete_cache(f"todos:{user_id}")
    
    return new_todo


def update_todo_service(user_id: str, todo_id: str, data: dict):
    # ... existing update logic ...
    
    # Invalidate caches
    delete_cache(f"todos:{user_id}")
    delete_cache(f"todo:{todo_id}")
    
    return {"msg": "Todo updated successfully"}


def delete_todo_service(user_id: str, todo_id: str):
    # ... existing delete logic ...
    
    # Invalidate caches
    delete_cache(f"todos:{user_id}")
    delete_cache(f"todo:{todo_id}")
    
    return {"msg": "Todo deleted successfully"}
```

---

### Use Case 3: JWT Token Blacklist (Logout)

**Where:** `src/utils/jwt.py` and a new logout endpoint

**Why:** Allow users to logout by revoking their tokens.

**Current problem:** The `BLACKLIST = set()` in `jwt.py` is in-memory and gets cleared on restart.

**Solution:** Store blacklisted tokens in Redis.

**Update `src/utils/jwt.py`:**

```python
from src.config import settings
from datetime import datetime, timedelta
from typing import Dict, Any
import jwt
from src.utils.redis_client import redis_client  # NEW


JWT_SECRET = settings.jwt_secret_key
JWT_ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_access_token_expire_minutes

# Remove the in-memory BLACKLIST
# BLACKLIST = set()  # OLD - don't use this anymore


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
    Also checks Redis blacklist.
    """
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    jti = payload.get("jti")
    
    # NEW: Check Redis blacklist instead of in-memory set
    if redis_client.exists(f"blacklist:{jti}"):
        raise jwt.InvalidTokenError("Token revoked")
    
    return payload


def revoke_jti(jti: str, exp: int) -> None:
    """
    Add a JTI to the blacklist in Redis.
    
    Args:
        jti: Token ID to revoke
        exp: Token expiration timestamp (to set TTL)
    """
    # Calculate remaining time until expiry
    now = int(datetime.utcnow().timestamp())
    ttl = exp - now
    
    if ttl > 0:
        # Store in Redis with TTL matching token expiry
        redis_client.setex(f"blacklist:{jti}", ttl, "revoked")
```

**Add logout endpoint in `src/auth/routes/auth.py`:**

```python
from fastapi import APIRouter, Depends
from src.auth.services.auth import register_user_service, login_user_service
from src.auth.schema import RegisterUser, LoginUser
from src.auth.services.dependencies import get_current_user  # NEW
from src.utils.jwt import decode_token, revoke_jti  # NEW
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # NEW

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}}
)

security = HTTPBearer()  # NEW

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
```

---

### Use Case 4: Rate Limiting

**Where:** Create a new dependency in `src/utils/rate_limiter.py`

**Why:** Prevent abuse by limiting requests per user/IP.

**Create `src/utils/rate_limiter.py`:**

```python
from fastapi import Request, HTTPException, status
from src.utils.redis_client import redis_client
from src.utils.logger import logger

log = logger()


def rate_limit(key_prefix: str, max_requests: int = 10, window: int = 60):
    """
    Rate limiting dependency.
    
    Args:
        key_prefix: Prefix for the rate limit key (e.g., "auth" or "todo")
        max_requests: Maximum requests allowed in the window
        window: Time window in seconds
    """
    async def check_rate_limit(request: Request):
        # Use IP address as identifier (or user_id if authenticated)
        client_ip = request.client.host
        key = f"rate_limit:{key_prefix}:{client_ip}"
        
        try:
            # Increment counter
            current = redis_client.incr(key)
            
            # Set expiry on first request
            if current == 1:
                redis_client.expire(key, window)
            
            # Check if limit exceeded
            if current > max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {window} seconds."
                )
            
            log.info(f"Rate limit check: {key} = {current}/{max_requests}")
            
        except redis.ConnectionError:
            # If Redis is down, allow the request (fail open)
            log.warning("Redis unavailable, skipping rate limit")
            pass
    
    return check_rate_limit
```

**Use rate limiting in routes:**

```python
from fastapi import APIRouter, Depends
from src.utils.rate_limiter import rate_limit

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", dependencies=[Depends(rate_limit("login", max_requests=5, window=60))])
def login(user: LoginUser):
    """
    Login with rate limiting: max 5 attempts per minute.
    """
    return login_user_service(user)


@router.post("/register", dependencies=[Depends(rate_limit("register", max_requests=3, window=3600))])
def register(user: RegisterUser):
    """
    Register with rate limiting: max 3 registrations per hour per IP.
    """
    return register_user_service(user)
```

---

## Step 7: Testing Redis Integration

Create `test_redis.py` to verify Redis works:

```python
"""
Test Redis connection and basic operations.
"""
from src.utils.redis_client import redis_client, set_cache, get_cache, delete_cache

def test_connection():
    print("Testing Redis connection...")
    try:
        response = redis_client.ping()
        if response:
            print("✅ Redis is connected!")
        else:
            print("❌ Redis ping failed")
    except Exception as e:
        print(f"❌ Redis connection error: {e}")


def test_cache_operations():
    print("\nTesting cache operations...")
    
    # Set cache
    test_data = {"name": "Alice", "email": "alice@example.com"}
    set_cache("test:user:1", test_data, expire=60)
    print("✅ Set cache: test:user:1")
    
    # Get cache
    cached = get_cache("test:user:1")
    if cached == test_data:
        print("✅ Get cache: data matches")
    else:
        print(f"❌ Get cache: data mismatch - {cached}")
    
    # Delete cache
    delete_cache("test:user:1")
    cached_after_delete = get_cache("test:user:1")
    if cached_after_delete is None:
        print("✅ Delete cache: key removed")
    else:
        print("❌ Delete cache: key still exists")


if __name__ == "__main__":
    test_connection()
    test_cache_operations()
```

Run it:
```bash
python test_redis.py
```

---

## Step 8: Update Docker Compose (Optional)

If using Docker, update `docker-compose.yaml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    volumes:
      - .:/app

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

---

## Step 9: Best Practices and Tips

### Cache Invalidation Strategy

1. **Time-based expiration**: Set reasonable TTLs (e.g., 5-10 minutes for todos, 1 hour for user profiles)
2. **Explicit invalidation**: Delete cache when data changes (create/update/delete operations)
3. **Cache keys naming**: Use consistent patterns:
   - `user:{user_id}` for user data
   - `todos:{user_id}` for todo lists
   - `todo:{todo_id}` for individual todos
   - `blacklist:{jti}` for revoked tokens

### Error Handling

Always handle Redis errors gracefully:

```python
try:
    cached = get_cache(key)
    if cached:
        return cached
except Exception as e:
    log.warning(f"Redis error, falling back to database: {e}")

# Fall back to database if Redis fails
return database_query()
```

### Monitoring

Check Redis health in your health endpoint:

```python
@app.get("/health")
def health_check():
    redis_status = "ok"
    try:
        redis_client.ping()
    except:
        redis_status = "down"
    
    return {
        "status": "ok",
        "redis": redis_status,
        "message": "Todo API is running"
    }
```

---

## Common Issues and Troubleshooting

### Issue 1: Connection Refused

**Error:** `redis.exceptions.ConnectionError: Error connecting to localhost:6379`

**Solution:**
- Make sure Redis server is running: `redis-cli ping`
- Check if Redis is listening on the right port: `netstat -an | grep 6379`
- Verify `REDIS_HOST` and `REDIS_PORT` in `.env`

### Issue 2: Authentication Failed

**Error:** `NOAUTH Authentication required`

**Solution:**
- Add password to Redis config and update `.env`:
  ```env
  REDIS_PASSWORD=your_password
  ```

### Issue 3: Data Not Persisting

**Problem:** Data disappears after Redis restart

**Solution:**
- Redis is in-memory by default. For persistence, start Redis with AOF:
  ```bash
  redis-server --appendonly yes
  ```

### Issue 4: Memory Issues

**Problem:** Redis uses too much memory

**Solution:**
- Set maxmemory and eviction policy in Redis config:
  ```bash
  redis-cli CONFIG SET maxmemory 256mb
  redis-cli CONFIG SET maxmemory-policy allkeys-lru
  ```

---

## Summary Checklist

When implementing Redis in your project:

- [ ] Install Redis server (local, Docker, or cloud)
- [ ] Add `redis` package to `requirements.txt`
- [ ] Update `.env` with Redis connection settings
- [ ] Update `src/config.py` with Redis configuration
- [ ] Create `src/utils/redis_client.py` for Redis utilities
- [ ] Implement caching in services (user data, todos)
- [ ] Move JWT blacklist from memory to Redis
- [ ] Add logout endpoint using Redis blacklist
- [ ] (Optional) Add rate limiting
- [ ] Test Redis connection with `test_redis.py`
- [ ] Update health check endpoint to include Redis status
- [ ] Document cache invalidation strategy

---

## Next Steps

After implementing Redis:

1. **Monitor performance**: Use Redis CLI to monitor operations:
   ```bash
   redis-cli monitor
   ```

2. **View cached keys**:
   ```bash
   redis-cli KEYS "*"
   ```

3. **Check memory usage**:
   ```bash
   redis-cli INFO memory
   ```

4. **Set up Redis in production**: Use managed services with replication and automatic failover

5. **Consider Redis Cluster**: For high availability and scalability

---

This guide covers the most common Redis use cases. Start with simple caching, then add more advanced features like rate limiting and session management as needed.
