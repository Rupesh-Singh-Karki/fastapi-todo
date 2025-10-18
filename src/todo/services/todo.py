from fastapi import HTTPException, status
from datetime import datetime
from bson import ObjectId
from src.utils.db import db

todo_collection = db["todos"]

def create_todo_service(user_id: str, heading: str, task: str):
    now = datetime.utcnow()
    new_todo = {
        "user_id": ObjectId(user_id),
        "heading": heading,
        "task": task,
        "completed": False,
        "created_at": now,
        "updated_at": now
    }
    result = todo_collection.insert_one(new_todo)
    new_todo["_id"] = result.inserted_id
    return {
        "id": str(new_todo["_id"]),
        "heading": new_todo["heading"],
        "task": new_todo["task"],
        "completed": new_todo["completed"],
        "created_at": new_todo["created_at"].isoformat(),
        "updated_at": new_todo["updated_at"].isoformat()
    }

def get_all_todos_service(user_id: str):
    todos = list(todo_collection.find({"user_id": ObjectId(user_id)}))
    result = []
    for t in todos:
        result.append({
            "id": str(t["_id"]),
            "heading": t["heading"],
            "task": t["task"],
            "completed": t["completed"],
            "created_at": t["created_at"].isoformat() if isinstance(t["created_at"], datetime) else t["created_at"],
            "updated_at": t["updated_at"].isoformat() if isinstance(t["updated_at"], datetime) else t["updated_at"]
        })
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
        "updated_at": todo["updated_at"].isoformat() if isinstance(todo["updated_at"], datetime) else todo["updated_at"]
    }

def update_todo_service(user_id: str, todo_id: str, data: dict):
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = todo_collection.update_one(
        {"_id": ObjectId(todo_id), "user_id": ObjectId(user_id)},
        {"$set": {**data, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Todo not found or not authorized")
    return {"msg": "Todo updated successfully"}

def delete_todo_service(user_id: str, todo_id: str):
    result = todo_collection.delete_one({"_id": ObjectId(todo_id), "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Todo not found or not authorized")
    return {"msg": "Todo deleted successfully"}