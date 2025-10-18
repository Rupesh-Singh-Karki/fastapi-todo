# Learning Guide — Todo Project (Beginner Friendly)

This guide explains the key pieces of the Todo Project so a beginner can understand how it works and where to look in the code. The explanations are intentionally simple and practical.

Project layout (important folders/files):

- `src/` — main application code.
  - `utils/` — helper utilities (database connection, JWT helpers, logger, Redis config).
  - `auth/` — authentication (models, schemas, routes, services).
  - `todo/` — todo feature (models, schemas, routes, services).
  - `main.py` — FastAPI app and route inclusion.
- `learning/README.md` — this file.
- `.env` — configuration values (database URI, JWT secret, etc.)


## How FastAPI is structured here

- Routes (in `src/*/routes/*.py`) define the HTTP endpoints (URLs) and how incoming requests are handled.
- Services (in `src/*/services/*.py`) contain the business logic: talk to the database, validate data, and return results. Routes call services.
- Schemas (Pydantic models in `src/*/schema.py`) define what data the API accepts (input) and returns (output).
- `utils/db.py` manages the database connection and provides collections that services use.


## Database (MongoDB)

Where to look:
- `src/utils/db.py` — sets up the connection to MongoDB using a URI from `.env`, exposes `db` and collection helpers.
- `.env` — contains `DB_URI`, `MONGO_DB`, `TODO_COLLECTION`, and `USER_COLLECTION`.

How it works (simple):
- The app reads the `DB_URI` and `MONGO_DB` values from `.env`.
- The `db` object is a MongoDB client that allows reading/writing documents.
- Collections are like tables: `users` and `todos` store user and todo documents.

Tips for beginners:
- Use MongoDB Atlas or a local MongoDB server and put the connection string in `.env`.
- Document IDs are stored in the `_id` field and are `ObjectId` types.


## JWT (JSON Web Tokens) Authentication

Where to look:
- `src/utils/jwt.py` — functions for creating and decoding JWTs.
- `src/auth/services/auth.py` — `login` function creates the access token.
- `src/auth/services/dependencies.py` — `get_current_user` decodes the token on protected routes.
- `.env` — `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`.

How it works (simple):
- When a user logs in successfully, the server creates a JWT containing the user's id (`sub` claim) and an expiry time (`exp`).
- The client stores that token and sends it in an `Authorization: Bearer <token>` header for protected routes.
- `get_current_user` reads the token, decodes it, checks it is not expired, then finds the corresponding user.

Security tips:
- Keep `JWT_SECRET_KEY` secret and do not commit it to version control.
- Use HTTPS in production.
- Tokens expire — users need to login again after expiry.


## Todo Feature — Services and Routes

Where to look:
- `src/todo/routes/todo.py` — route definitions for creating, updating, listing, and deleting todos.
- `src/todo/services/todo.py` — service functions that actually manipulate todo documents in MongoDB.
- `src/todo/schema.py` — Pydantic models for creating/updating todos and response model.

What happens when you create a todo (flow):
1. Client calls `POST /todo/` with a JSON body containing `heading` and `task`.
2. The route depends on `get_current_user` so the request must include a valid JWT.
3. The route calls `create_todo_service` with the `user_id`, heading, and task.
4. The service inserts a document into the `todos` collection and sets `created_at` and `updated_at` automatically.
5. The service returns the newly created todo (with `id`, `created_at`, and `updated_at`).

Why timestamps and id are automatic:
- This prevents clients from manipulating internal fields like `id`, `created_at`, and `updated_at`.
- The backend sets these values to ensure consistency.


## Auth Feature — Services and Routes

Where to look:
- `src/auth/routes/auth.py` — registers `/auth/register` and `/auth/login` endpoints.
- `src/auth/services/auth.py` — logic for registering users and generating JWTs for login.
- `src/auth/schema.py` — Pydantic models for register/login payloads.

Register flow:
1. Client calls `POST /auth/register` with `name`, `email`, `password`.
2. Service hashes the password and inserts a new user document.

Login flow:
1. Client calls `POST /auth/login` with `email`, `password`.
2. Service verifies the password and on success calls `create_access_token` with the user's `_id`.
3. The response includes `access_token` and `token_type`.


## Dependencies (auth verification)

Where to look:
- `src/auth/services/dependencies.py`

What it does:
- Uses `HTTPBearer` to read the `Authorization` header.
- Decodes the JWT and fetches the user from the database using the `sub` claim (user `_id`).
- If the token is expired or invalid, it raises a 401 error.


## How to run the project (local development)

Make sure you have Python 3.10+ and a virtual environment:

```bash
cd /home/mrzoro/Desktop/Practice/Todo-Project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Make sure .env is configured with DB_URI and JWT_SECRET_KEY
uvicorn src.main:app --reload
```

Open the docs: http://127.0.0.1:8000/docs

Try these steps:
1. Register a new user (POST `/auth/register`).
2. Login (POST `/auth/login`) to get `access_token`.
3. Click the Authorize button in `/docs` and paste the token.
4. Create a todo (POST `/todo/`) with `heading` and `task`.
5. List todos (GET `/todo/`).


## Common issues & troubleshooting

- Token expired immediately: Ensure you restarted the server after code changes. Re-login to get a fresh token.
- `User not found` after login: Ensure the token `sub` contains the user's `_id` and `get_current_user` queries `_id` field.
- Database connection errors: Verify `DB_URI` and network access to MongoDB Atlas or local MongoDB.


## Next steps for learning (suggestions)
- Add tests for auth and todo services in `tests/`.
- Implement token refresh (refresh tokens) to avoid logging in frequently.
- Add role-based auth (admin/user) if you need more granular permissions.
- Add pagination for `get_all_todos_service` if you expect many todos.


---

If you want, I can also:
- Add a small `learning/quickstart.sh` script to automate env setup and run the server.
- Add example curl commands for each endpoint.

Tell me which extra thing you'd like next.