from fastapi import HTTPException, status
from src.utils.db import user_collection, hash_password, verify_password
from src.auth.schema import RegisterUser, LoginUser
from src.utils.jwt import create_access_token

def register_user_service(user: RegisterUser):
    existing_user = user_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_pw = hash_password(user.password)
    new_user = {
        "name": user.name,
        "email": user.email,
        "password": hashed_pw
    }

    result = user_collection.insert_one(new_user)
    return {"msg": "User registered successfully", "user_id": str(result.inserted_id)}

def login_user_service(user: LoginUser):
    db_user = user_collection.find_one({"email": user.email})

    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token(identity=str(db_user["_id"]))
    return {
        "msg": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "name": db_user["name"],
            "email": db_user["email"]
        }
    }