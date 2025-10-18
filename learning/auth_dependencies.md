# `src/auth/services/dependencies.py` — Beginner Explanation

Purpose
- Provides `get_current_user`, a dependency used by routes to protect endpoints and automatically fetch the authenticated user.
- This function reads the JWT sent by the client, validates it, and loads the corresponding user from the database.

Key parts

- `security = HTTPBearer()`
  - Reads the `Authorization: Bearer <token>` header from requests.

- `get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security))`
  - Extracts the token string from `credentials.credentials`.
  - Calls `decode_token(token)` to verify the JWT and get its payload.
  - Reads `sub` from the token payload (this project stores the user `_id` there).
  - Converts `sub` to an `ObjectId` and queries the `users` collection.
  - Returns the user document to the route. If the token is invalid or expired, it raises a `401 Unauthorized`.

Why use dependencies?
- FastAPI dependencies are a clean way to reuse logic like authentication or database sessions across multiple routes. Routes can simply declare `current_user=Depends(get_current_user)` and get the user automatically.

Common issues
- Sending the token in the wrong place: ensure you send it in the `Authorization` header as `Bearer <token>`.
- Using an expired token: tokens have an expiry (`exp`) — if expired the dependency will raise a 401.
- Incorrect `sub` value: this project expects the token `sub` to contain the user's `_id` so `get_current_user` can find the user by `_id`.

How to use with routes
- In `src/todo/routes/todo.py` you will see endpoints that have `current_user=Depends(get_current_user)`. This ensures only authenticated users can call those endpoints.