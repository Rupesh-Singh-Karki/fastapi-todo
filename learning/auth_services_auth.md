
# `src/auth/services/auth.py` — Beginner Explanation (Line-by-line)

This file contains the logic for registering and logging in users. Below you'll find the actual code (as used in the project) and a clear explanation of what each part does.

---

Code (complete file):

```python
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
```

Line-by-line explanation:

1. `from fastapi import HTTPException, status`
  - Imports FastAPI utilities to raise proper HTTP errors with status codes.

2. `from src.utils.db import user_collection, hash_password, verify_password`
  - `user_collection`: a MongoDB collection object to read/write users.
  - `hash_password` and `verify_password`: helper functions for secure password hashing.

3. `from src.auth.schema import RegisterUser, LoginUser`
  - These are Pydantic models describing the expected input shapes for register and login.

4. `from src.utils.jwt import create_access_token`
  - Function to create a signed JWT used for authentication.

5. `def register_user_service(user: RegisterUser):`
  - Defines a function that accepts the validated `RegisterUser` data and registers a new user.

6. `existing_user = user_collection.find_one({"email": user.email})`
  - Checks if a user with the provided email already exists in the DB.

7-10. `if existing_user: ... raise HTTPException(...)`
  - If the email is already in use, raise a 400 Bad Request with a helpful message.

11. `hashed_pw = hash_password(user.password)`
  - Hash the plain password using a secure algorithm (Argon2 via passlib in this project).

12-16. `new_user = { ... }`
  - Build a dictionary representing the new user document to insert into MongoDB. We store the hashed password, not the plain text.

17. `result = user_collection.insert_one(new_user)`
  - Insert the new user in the DB; `result.inserted_id` is the generated MongoDB `_id`.

18. `return {"msg": ..., "user_id": str(result.inserted_id)}`
  - Return a simple response confirming registration and the user's id as a string.

19. `def login_user_service(user: LoginUser):`
  - Defines the login function which returns a token if credentials are correct.

20. `db_user = user_collection.find_one({"email": user.email})`
  - Look up the user by email.

21-25. `if not db_user or not verify_password(...): raise HTTPException(...)`
  - If there's no user or the password check fails, raise 401 Unauthorized.

26. `token = create_access_token(identity=str(db_user["_id"]))`
  - Create a JWT that stores the user's `_id` string in its `sub` claim. This token will be used to authenticate future requests.

27-34. `return {"msg": ..., "access_token": token, ...}`
  - Return the token and some basic user info. The `token_type` field is `bearer`, which clients and Swagger UI use when sending the token.

Tips for beginners:
- Always hash passwords. Never store plain text.
- If you change the token payload or secret, existing tokens may become invalid.
- Use the returned `user_id` for debugging, but never expose full password hashes in responses.

---

If you'd like, I can add inline comments directly into a `.py` copy for easier reading in an editor. 