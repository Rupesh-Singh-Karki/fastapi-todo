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