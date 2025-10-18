
# `src/utils/db.py` — Beginner Explanation (Line-by-line)

This file sets up the MongoDB connection and provides small helpers for password hashing/verification. Below is the code and a line-by-line walkthrough.

---

Code (complete file):

```python
from pymongo import MongoClient
from src.config import settings
from pymongo.errors import DuplicateKeyError
from passlib.context import CryptContext
import hashlib

MONGO_URL = settings.db_uri
MONGO_DB = settings.mongo_db
TODO_COLLECTION = settings.todo_collection
USER_COLLECTION = settings.user_collection

client = MongoClient(MONGO_URL)
db = client[MONGO_DB]
todo_collection = db[TODO_COLLECTION]
user_collection = db[USER_COLLECTION]

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
   """
   Hash a password using argon2.
   """
   return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
   """
   Verify a password against a hashed password.
   """
   return pwd_context.verify(plain_password, hashed_password)


def serialize_todo(todo) -> dict:
   return {
      "id": str(todo["_id"]),
      "title": todo["title"],
      "description": todo["description"],
      "completed": todo["completed"],
   }
```

Line-by-line explanation:

1. `from pymongo import MongoClient`
  - `MongoClient` creates a connection to a MongoDB server.

2. `from src.config import settings`
  - Reads configuration values (like `DB_URI`) from the project's settings.

3. `from pymongo.errors import DuplicateKeyError`
  - Importing specific exceptions can help you handle DB errors later.

4. `from passlib.context import CryptContext`
  - `passlib` provides password hashing algorithms and helpers.

5. `import hashlib`
  - Imported but not used in this snippet; can be removed or used for other hash-related tasks.

6-9. `MONGO_URL = settings.db_uri` etc.
  - Load database configuration from `.env` via `settings`.

10-13. `client = MongoClient(MONGO_URL)` ...
  - Create the client and select the database and named collections.

14. `pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")`
  - Configure password hashing to use Argon2, which is modern and secure.

15-18. `def hash_password(password: str) -> str:`
  - Hash a plain password string using Argon2.

19-23. `def verify_password(plain_password: str, hashed_password: str) -> bool:`
  - Verify a plaintext password against a stored hash.

24-30. `def serialize_todo(todo) -> dict:`
  - Small helper to convert a DB document to a JSON-friendly dict. Note: keys `title`/`description` may differ from the project's todo model; treat this as an example.

Tips for beginners:
- If you see `ServerSelectionTimeoutError`, your `DB_URI` might be wrong or network access to the DB is blocked.
- Make sure to convert ObjectIds to strings before returning them in API responses.

---
