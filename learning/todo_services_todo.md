
# `src/todo/services/todo.py` — Beginner Explanation (Line-by-line)

This file contains the main business logic for managing todos. Below is the full source code and a numbered explanation for each line or block.

---

Code (complete file):

```python
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
```

Line-by-line explanation:

1. `from fastapi import HTTPException, status`
   - Used to raise HTTP errors with status codes when things go wrong (e.g., 404 Not Found).

2. `from datetime import datetime`
   - For timestamps; this file uses `datetime.utcnow()` to create consistent UTC timestamps.

3. `from bson import ObjectId`
   - Convert string ids into MongoDB `ObjectId` for queries.

4. `from src.utils.db import db`
   - Import the `db` object from the project's DB utility module.

5. `todo_collection = db["todos"]`
   - Shortcut to the `todos` collection so the rest of the file can use it.

6-18. `def create_todo_service(...)`
   - `now = datetime.utcnow()` — capture a single timestamp for both `created_at` and `updated_at`.
   - `new_todo = { ... }` — prepare the todo document, converting `user_id` to an `ObjectId`.
   - `result = todo_collection.insert_one(new_todo)` — insert into MongoDB and get the inserted id.
   - `new_todo["_id"] = result.inserted_id` — attach the id to the object.
   - Return a dict with string `id` and ISO-formatted timestamps so JSON can send them.

19-29. `def get_all_todos_service(user_id: str):`
   - Query todos by `user_id` (converted to `ObjectId`).
   - Iterate and convert each document to a JSON-friendly dict (string id, ISO timestamps).

30-42. `def get_todo_service(user_id: str, todo_id: str):`
   - Find a todo matching both `_id` and `user_id` to ensure users can only access their own todos.
   - If not found, raise 404.
   - If found, return a JSON-friendly dict with ISO timestamps.

43-54. `def update_todo_service(user_id: str, todo_id: str, data: dict):`
   - If `data` is empty, reject with 400 to avoid accidental empty updates.
   - Use `update_one` with `$set` and add `updated_at` timestamp.
   - If no document matched, raise 404.

55-60. `def delete_todo_service(user_id: str, todo_id: str):`
   - Delete the document matching `_id` and `user_id`. If none deleted, raise 404.

Common beginner pitfalls:

- When returning timestamps, make them strings (ISO) so clients can parse them easily.
- Always use both `_id` and `user_id` filters for security: otherwise users might access others' todos.

---
