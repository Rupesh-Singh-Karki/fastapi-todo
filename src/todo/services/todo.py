from fastapi import HTTPException, status
from datetime import datetime
from typing import Optional
from bson import ObjectId
from src.utils.db import db
from src.utils.redis_client import get_cache, set_cache, delete_cache

todo_collection = db["todos"]

# If you don’t delete the cache after any sort of updation, eg -  get_all_todos_service will still return [todo1, todo2] from Redis → outdated.

def create_todo_service(user_id: str, heading: str, task: str, completion_time: Optional[datetime] = None):
    now = datetime.utcnow()
    new_todo = {
        "user_id": ObjectId(user_id),
        "heading": heading,
        "task": task,
        "completed": False,
        "created_at": now,
        "updated_at": now,
        "completion_time": completion_time,
        "reminder_sent": False
    }
    result = todo_collection.insert_one(new_todo)
    new_todo["_id"] = result.inserted_id
    
    # Invalidate cache
    delete_cache(f"todos:{user_id}")

    return {
        "id": str(new_todo["_id"]),
        "heading": new_todo["heading"],
        "task": new_todo["task"],
        "completed": new_todo["completed"],
        "created_at": new_todo["created_at"].isoformat(),
        "updated_at": new_todo["updated_at"].isoformat(),
        "completion_time": new_todo["completion_time"].isoformat() if new_todo["completion_time"] else None,
        "reminder_sent": new_todo["reminder_sent"]
    }

def get_all_todos_service(user_id: str):
    # Try cache first
    cache_key = f"todos:{user_id}"
    cached_todos = get_cache(cache_key)
    
    if cached_todos:
        return cached_todos

    todos = list(todo_collection.find({"user_id": ObjectId(user_id)}))
    result = []
    for t in todos:
        result.append({
            "id": str(t["_id"]),
            "heading": t["heading"],
            "task": t["task"],
            "completed": t["completed"],
            "created_at": t["created_at"].isoformat() if isinstance(t["created_at"], datetime) else t["created_at"],
            "updated_at": t["updated_at"].isoformat() if isinstance(t["updated_at"], datetime) else t["updated_at"],
            "completion_time": t["completion_time"].isoformat() if t.get("completion_time") else None,
            "reminder_sent": t.get("reminder_sent", False)
        })

    # Cache the result for future requests
    set_cache(cache_key, result, expire=300)  # Cache for 5 minutes
    return result

def get_todo_service(user_id: str, todo_id: str):
    todo = todo_collection.find_one({"_id": ObjectId(todo_id), "user_id": ObjectId(user_id)})
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    return {
        "id": str(todo["_id"]),
        "heading": todo["heading"],
        "task": todo["task"],
        "completed": todo["completed"],
        "created_at": todo["created_at"].isoformat() if isinstance(todo["created_at"], datetime) else todo["created_at"],
        "updated_at": todo["updated_at"].isoformat() if isinstance(todo["updated_at"], datetime) else todo["updated_at"],
        "completion_time": todo["completion_time"].isoformat() if todo.get("completion_time") else None,
        "reminder_sent": todo.get("reminder_sent", False)
    }

def update_todo_service(user_id: str, todo_id: str, data: dict):
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    if data.get("completed") == True:
        data["reminder_sent"] = True #prevent future reminders
    
    result = todo_collection.update_one(
        {"_id": ObjectId(todo_id), "user_id": ObjectId(user_id)},
        {"$set": {**data, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Todo not found or not authorized")
    
    # Invalidate cache
    delete_cache(f"todos:{user_id}")
    delete_cache(f"todo:{todo_id}")

    return {"msg": "Todo updated successfully"}

def delete_todo_service(user_id: str, todo_id: str):
    result = todo_collection.delete_one({"_id": ObjectId(todo_id), "user_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Todo not found or not authorized")

    # Invalidate cache
    delete_cache(f"todos:{user_id}")
    delete_cache(f"todo:{todo_id}")

    return {"msg": "Todo deleted successfully"}


# | Action     | Cache to delete                     | Reason                                                              |
# | ---------- | ----------------------------------- | ------------------------------------------------------------------- |
# | **Create** | `todos:{user_id}`                   | Only the list of todos changes; new todo has no cache yet           |
# | **Update** | `todos:{user_id}`, `todo:{todo_id}` | Both the list and individual todo cache may be stale                |
# | **Delete** | `todos:{user_id}`, `todo:{todo_id}` | Same as update: remove stale data for both list and the single todo |
