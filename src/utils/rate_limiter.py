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


# This code implements a per-IP rate limiter using Redis:
# Generates a unique Redis key per IP and endpoint.
# Increments a request counter in Redis.
# Sets a TTL to reset the counter after window seconds.
# Blocks requests exceeding max_requests.
# Logs activity and gracefully handles Redis downtime.