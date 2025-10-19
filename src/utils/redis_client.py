"""
Redis client utility for caching and token blacklisting.
Configured for cloud Redis services (Redis Cloud, Upstash, etc.)
"""

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
    Get Redis client instance and verify connection.
    Returns None if Redis is unavailable.
    """
    try:
        redis_client.ping()
        return redis_client
    except redis.ConnectionError as e:
        log.error(f"Failed to connect to Redis: {e}")
        return None
    except Exception as e:
        log.error(f"Redis error: {e}")
        return None


def set_cache(key: str, value: any, expire: int = 300):
    """
    Set a cache value in Redis with expiration (default 5 minutes).
    
    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        expire: Expiration time in seconds
    
    Returns:
        True if successful, False otherwise
    """
    try:
        redis_client.setex(key, expire, json.dumps(value))
        log.info(f"Cached: {key} (expires in {expire}s)")
        return True
    except Exception as e:
        log.error(f"Redis cache set error for key '{key}': {e}")
        return False


def get_cache(key: str):
    """
    Get a cached value from Redis.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None if not found/error
    """
    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        log.error(f"Redis cache get error for key '{key}': {e}")
        return None


def delete_cache(key: str):
    """
    Delete a cache key from Redis.
    
    Args:
        key: Cache key to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        redis_client.delete(key)
        log.info(f"Deleted cache: {key}")
        return True
    except Exception as e:
        log.error(f"Redis cache delete error for key '{key}': {e}")
        return False


def cache_exists(key: str) -> bool:
    """
    Check if a cache key exists.
    
    Args:
        key: Cache key to check
        
    Returns:
        True if exists, False otherwise
    """
    try:
        return redis_client.exists(key) > 0
    except Exception as e:
        log.error(f"Redis exists check error for key '{key}': {e}")
        return False


def invalidate_pattern(pattern: str):
    """
    Delete all keys matching a pattern.
    Useful for bulk cache invalidation.
    
    Args:
        pattern: Redis key pattern (e.g., "todos:*", "user:123:*")
        
    Example:
        invalidate_pattern("todos:*")  # Clear all todo caches
    """
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            log.info(f"Invalidated {len(keys)} keys matching pattern: {pattern}")
            return len(keys)
        return 0
    except Exception as e:
        log.error(f"Redis pattern invalidation error for '{pattern}': {e}")
        return 0


# JWT Token Blacklist Functions

def blacklist_token(jti: str, exp: int):
    """
    Add a JWT token ID (jti) to the blacklist.
    Used for logout functionality.
    
    Args:
        jti: JWT token ID to blacklist
        exp: Token expiration timestamp (Unix timestamp)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from datetime import datetime
        now = int(datetime.utcnow().timestamp())
        ttl = exp - now
        
        if ttl > 0:
            # Store in Redis with TTL matching token expiry
            redis_client.setex(f"blacklist:{jti}", ttl, "revoked")
            log.info(f"Blacklisted token: {jti} (expires in {ttl}s)")
            return True
        else:
            log.warning(f"Token already expired: {jti}")
            return False
    except Exception as e:
        log.error(f"Failed to blacklist token {jti}: {e}")
        return False


def is_token_blacklisted(jti: str) -> bool:
    """
    Check if a JWT token ID is blacklisted.
    
    Args:
        jti: JWT token ID to check
        
    Returns:
        True if blacklisted, False otherwise
    """
    try:
        return redis_client.exists(f"blacklist:{jti}") > 0
    except Exception as e:
        log.error(f"Failed to check blacklist for token {jti}: {e}")
        # Fail open: if Redis is down, allow the request
        return False


# Rate Limiting Functions

def check_rate_limit(key: str, max_requests: int, window: int) -> bool:
    """
    Check if a rate limit has been exceeded.
    
    Args:
        key: Rate limit key (e.g., "rate_limit:login:192.168.1.1")
        max_requests: Maximum requests allowed in the window
        window: Time window in seconds
        
    Returns:
        True if under limit, False if exceeded
    """
    try:
        current = redis_client.incr(key)
        
        # Set expiry on first request
        if current == 1:
            redis_client.expire(key, window)
        
        return current <= max_requests
    except Exception as e:
        log.error(f"Rate limit check error for '{key}': {e}")
        # Fail open: if Redis is down, allow the request
        return True


def get_rate_limit_status(key: str) -> dict:
    """
    Get current rate limit status for a key.
    
    Args:
        key: Rate limit key
        
    Returns:
        Dictionary with current count and TTL
    """
    try:
        count = redis_client.get(key)
        ttl = redis_client.ttl(key)
        
        return {
            "count": int(count) if count else 0,
            "ttl": ttl if ttl > 0 else 0
        }
    except Exception as e:
        log.error(f"Failed to get rate limit status for '{key}': {e}")
        return {"count": 0, "ttl": 0}
