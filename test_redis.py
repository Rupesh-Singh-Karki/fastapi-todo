"""
Test Redis connection and basic operations.
This script helps verify your cloud Redis setup is working correctly.
"""

from src.utils.redis_client import (
    redis_client, 
    get_redis, 
    set_cache, 
    get_cache, 
    delete_cache,
    cache_exists,
    blacklist_token,
    is_token_blacklisted,
    check_rate_limit
)
from src.config import settings
import time

print("=" * 60)
print("Redis Connection Test")
print("=" * 60)
print(f"\nConnecting to: {settings.redis_url.split('@')[-1] if '@' in settings.redis_url else settings.redis_url}")
print()


def test_connection():
    """Test basic Redis connection."""
    print("1. Testing Redis connection...")
    try:
        response = redis_client.ping()
        if response:
            print("   ✅ Redis is connected!")
            
            # Get Redis info
            info = redis_client.info('server')
            print(f"   📊 Redis version: {info.get('redis_version', 'unknown')}")
            print(f"   📊 Redis mode: {info.get('redis_mode', 'unknown')}")
            return True
        else:
            print("   ❌ Redis ping failed")
            return False
    except Exception as e:
        print(f"   ❌ Redis connection error: {e}")
        print("\n💡 Troubleshooting:")
        print("   - Check your REDIS_URL in .env file")
        print("   - Verify Redis Cloud credentials")
        print("   - Ensure your IP is whitelisted (if required)")
        return False


def test_cache_operations():
    """Test cache set/get/delete operations."""
    print("\n2. Testing cache operations...")
    
    # Set cache
    test_data = {
        "name": "Alice",
        "email": "alice@example.com",
        "todos_count": 5
    }
    
    print("   → Setting cache: test:user:1")
    success = set_cache("test:user:1", test_data, expire=60)
    if not success:
        print("   ❌ Failed to set cache")
        return False
    
    # Get cache
    print("   → Getting cache: test:user:1")
    cached = get_cache("test:user:1")
    if cached == test_data:
        print("   ✅ Cache retrieved successfully")
        print(f"   📦 Data: {cached}")
    else:
        print(f"   ❌ Cache mismatch - expected: {test_data}, got: {cached}")
        return False
    
    # Check exists
    print("   → Checking if cache exists")
    if cache_exists("test:user:1"):
        print("   ✅ Cache exists check passed")
    else:
        print("   ❌ Cache exists check failed")
        return False
    
    # Delete cache
    print("   → Deleting cache: test:user:1")
    delete_cache("test:user:1")
    cached_after_delete = get_cache("test:user:1")
    if cached_after_delete is None:
        print("   ✅ Cache deleted successfully")
    else:
        print("   ❌ Cache still exists after deletion")
        return False
    
    return True


def test_expiration():
    """Test cache expiration."""
    print("\n3. Testing cache expiration...")
    
    print("   → Setting cache with 3 second expiry")
    set_cache("test:expiry", {"temp": "data"}, expire=3)
    
    print("   → Checking immediately")
    if get_cache("test:expiry"):
        print("   ✅ Cache exists (as expected)")
    else:
        print("   ❌ Cache missing (unexpected)")
        return False
    
    print("   → Waiting 4 seconds...")
    time.sleep(4)
    
    print("   → Checking after expiration")
    if get_cache("test:expiry") is None:
        print("   ✅ Cache expired successfully")
    else:
        print("   ❌ Cache still exists (should be expired)")
        return False
    
    return True


def test_token_blacklist():
    """Test JWT token blacklist functionality."""
    print("\n4. Testing JWT token blacklist...")
    
    # Simulate a token ID
    test_jti = "test-token-12345"
    test_exp = int(time.time()) + 300  # Expires in 5 minutes
    
    print(f"   → Blacklisting token: {test_jti}")
    success = blacklist_token(test_jti, test_exp)
    if not success:
        print("   ❌ Failed to blacklist token")
        return False
    
    print("   → Checking if token is blacklisted")
    if is_token_blacklisted(test_jti):
        print("   ✅ Token blacklist check passed")
    else:
        print("   ❌ Token not found in blacklist")
        return False
    
    # Clean up
    delete_cache(f"blacklist:{test_jti}")
    print("   🧹 Cleaned up test token")
    
    return True


def test_rate_limiting():
    """Test rate limiting functionality."""
    print("\n5. Testing rate limiting...")
    
    rate_key = "test:rate_limit:192.168.1.1"
    max_requests = 5
    window = 60
    
    print(f"   → Testing rate limit: {max_requests} requests per {window}s")
    
    # Make requests
    for i in range(max_requests + 2):
        allowed = check_rate_limit(rate_key, max_requests, window)
        status = "✅ Allowed" if allowed else "❌ Blocked"
        print(f"   Request {i+1}: {status}")
        
        if i < max_requests and not allowed:
            print("   ❌ Request blocked before limit")
            return False
        
        if i >= max_requests and allowed:
            print("   ❌ Request allowed after limit")
            return False
    
    # Clean up
    delete_cache(rate_key)
    print("   🧹 Cleaned up rate limit key")
    print("   ✅ Rate limiting works correctly")
    
    return True


def test_complex_data():
    """Test caching complex nested data."""
    print("\n6. Testing complex data structures...")
    
    complex_data = {
        "user": {
            "id": "user123",
            "name": "John Doe",
            "email": "john@example.com"
        },
        "todos": [
            {
                "id": "todo1",
                "heading": "Buy groceries",
                "task": "Get milk and eggs",
                "completed": False,
                "created_at": "2025-10-19T10:00:00Z"
            },
            {
                "id": "todo2",
                "heading": "Finish project",
                "task": "Complete the Redis integration",
                "completed": True,
                "created_at": "2025-10-19T09:00:00Z"
            }
        ],
        "stats": {
            "total": 2,
            "completed": 1,
            "pending": 1
        }
    }
    
    print("   → Caching complex nested data")
    set_cache("test:complex", complex_data, expire=60)
    
    print("   → Retrieving complex data")
    retrieved = get_cache("test:complex")
    
    if retrieved == complex_data:
        print("   ✅ Complex data cached and retrieved correctly")
    else:
        print("   ❌ Data mismatch")
        return False
    
    # Clean up
    delete_cache("test:complex")
    print("   🧹 Cleaned up test data")
    
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Starting Redis Tests")
    print("=" * 60 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Connection", test_connection()))
    
    if results[0][1]:  # Only continue if connection works
        results.append(("Cache Operations", test_cache_operations()))
        results.append(("Cache Expiration", test_expiration()))
        results.append(("Token Blacklist", test_token_blacklist()))
        results.append(("Rate Limiting", test_rate_limiting()))
        results.append(("Complex Data", test_complex_data()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! Redis is ready to use.")
        print("\n📝 Next steps:")
        print("   1. Implement caching in your todo services")
        print("   2. Add JWT token blacklist for logout")
        print("   3. Add rate limiting to auth endpoints")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    run_all_tests()
