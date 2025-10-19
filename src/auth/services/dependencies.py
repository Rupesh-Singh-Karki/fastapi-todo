from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.utils.jwt import decode_token
from src.utils.db import user_collection
from bson import ObjectId
from src.utils.redis_client import get_cache, set_cache
import jwt

security = HTTPBearer()

#for auth verification making endpoints secure
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = decode_token(token)
        user_id = payload.get("sub")

        # Check cache first
        cached_key = f"user:{user_id}"
        cached_user = get_cache(cached_key)

        if cached_user:
            # Return cached user (convert _id back to ObjectId for consistency)
            cached_user["_id"] = ObjectId(cached_user["_id"])
            return cached_user
        
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        
        # Cache the user data for future requests
        # NEW: Cache the user for 10 minutes (600 seconds)
        user_to_cache = {
            "_id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"]
        }
        set_cache(cached_key, user_to_cache, expire=600)

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



# from src.utils.redis_client import delete_cache

# def update_user_profile(user_id: str, data: dict):
#     # Update user in database
#     result = user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": data})
    
#     # Invalidate cache
#     delete_cache(f"user:{user_id}")
    
#     return {"msg": "Profile updated"}