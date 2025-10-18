"""
Quick test script to verify JWT token generation
"""
from datetime import datetime
from src.utils.jwt import create_access_token, decode_token
import jwt

# Test token creation
test_user_id = "507f1f77bcf86cd799439011"  # Sample MongoDB ObjectId
print("Creating token...")
token = create_access_token(identity=test_user_id)
print(f"Token: {token}\n")

# Decode without verification to see payload
print("Token payload (raw):")
try:
    payload = jwt.decode(token, options={"verify_signature": False})
    print(f"  sub (user_id): {payload.get('sub')}")
    print(f"  iat (issued at): {datetime.fromtimestamp(payload.get('iat'))} UTC")
    print(f"  exp (expires at): {datetime.fromtimestamp(payload.get('exp'))} UTC")
    print(f"  jti (token id): {payload.get('jti')}")
    
    now = datetime.utcnow()
    exp_time = datetime.fromtimestamp(payload.get('exp'))
    time_diff = (exp_time - now).total_seconds() / 60
    print(f"\nToken valid for: {time_diff:.2f} minutes")
    
    # Try to decode with verification
    print("\nVerifying token...")
    verified_payload = decode_token(token)
    print("✅ Token is valid!")
    
except jwt.ExpiredSignatureError:
    print("❌ Token has already expired!")
except Exception as e:
    print(f"❌ Error: {e}")
