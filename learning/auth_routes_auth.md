
# `src/auth/routes/auth.py` — Beginner Explanation (Line-by-line)

This file exposes the HTTP endpoints for authentication. The code is short, so we'll show it and explain each part.

---

Code (complete file):

```python
from fastapi import APIRouter
from src.auth.services.auth import register_user_service, login_user_service
from src.auth.schema import RegisterUser, LoginUser

router = APIRouter(
   prefix="/auth",
   tags=["Authentication"],
   responses={404: {"description": "Not found"}}
)

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
```

Line-by-line explanation:

1. `from fastapi import APIRouter`
  - FastAPI's router object allows grouping routes and applying common prefixes/tags.

2. `from src.auth.services.auth import register_user_service, login_user_service`
  - Import the service functions that actually do the work of registration and login.

3. `from src.auth.schema import RegisterUser, LoginUser`
  - Pydantic models used to validate incoming request bodies automatically.

4-8. `router = APIRouter(...)`
  - Creates an `APIRouter` instance. `prefix='/auth'` means each route will start with `/auth` (e.g., `/auth/login`). `tags` are used by the docs UI.

9-13. `@router.post('/register') ...`
  - Declares a POST endpoint at `/auth/register`. The `user: RegisterUser` parameter tells FastAPI to read and validate the JSON body against `RegisterUser`.
  - The function returns whatever `register_user_service` returns.

14-18. `@router.post('/login') ...`
  - Declares a POST endpoint at `/auth/login`. Similar structure to register: the body is validated and passed to the service.

Why keep these functions short?
- Routes should be thin: accept HTTP requests, validate inputs (FastAPI + Pydantic), and pass data to services. This improves testability and separation of concerns.

Beginner tip
- Use the Swagger UI at `/docs` to exercise these endpoints interactively. FastAPI uses type hints and Pydantic to auto-generate input forms.

---

Let me know if you'd like inline comments added directly to the source file as well.