
# `src/todo/routes/todo.py` — Beginner Explanation (Line-by-line)

This file defines the HTTP endpoints for the Todo feature. Below is the code and a numbered explanation for each line or small block so beginners can follow along.

---

Code (complete file):

```python
from fastapi import APIRouter, Depends
from src.todo.schema import TodoCreate, TodoUpdate, Todo
from src.todo.services.todo import (
   create_todo_service,
   get_all_todos_service,
   get_todo_service,
   update_todo_service,
   delete_todo_service
)
from src.auth.services.dependencies import get_current_user

router = APIRouter(prefix="/todo", tags=["Todo"])

@router.post("/", response_model=Todo)
def create_todo(todo: TodoCreate, current_user=Depends(get_current_user)):
   return create_todo_service(str(current_user["_id"]), todo.heading, todo.task)

@router.get("/")
def get_all_todos(current_user=Depends(get_current_user)):
   return get_all_todos_service(str(current_user["_id"]))

@router.get("/{todo_id}", response_model=Todo)
def get_todo(todo_id: str, current_user=Depends(get_current_user)):
   return get_todo_service(str(current_user["_id"]), todo_id)

@router.put("/{todo_id}")
def update_todo(todo_id: str, todo: TodoUpdate, current_user=Depends(get_current_user)):
   # Only include fields that were actually provided
   update_data = todo.model_dump(exclude_unset=True)
   return update_todo_service(str(current_user["_id"]), todo_id, update_data)

@router.delete("/{todo_id}")
def delete_todo(todo_id: str, current_user=Depends(get_current_user)):
   return delete_todo_service(str(current_user["_id"]), todo_id)
```

Line-by-line explanation:

1-2. `from fastapi import APIRouter, Depends`
  - `APIRouter` groups routes under a common prefix and allows modular route organization.
  - `Depends` is used to declare route dependencies (e.g., authentication).

3. `from src.todo.schema import TodoCreate, TodoUpdate, Todo`
  - Import Pydantic models used for request validation and response serialization.

4-9. Import service functions from `src.todo.services.todo`.
  - These are the business logic functions that interact with the database.

10. `from src.auth.services.dependencies import get_current_user`
  - Import the authentication dependency that decodes JWT and returns the current user.

11. `router = APIRouter(prefix="/todo", tags=["Todo"])`
  - Create the router. All endpoints will be under `/todo`.

12-14. `@router.post("/", response_model=Todo)` and `create_todo(...)`
  - Declares `POST /todo/` which accepts `TodoCreate` body and depends on the authenticated user.
  - Calls `create_todo_service` with the user's id and todo data.

15-17. `@router.get("/")` and `get_all_todos(...)`
  - Declares `GET /todo/` which returns all todos for the authenticated user.

18-20. `@router.get("/{todo_id}", response_model=Todo)` and `get_todo(...)`
  - Declares `GET /todo/{todo_id}` to fetch a single todo by id for the authenticated user.

21-25. `@router.put("/{todo_id}")` and `update_todo(...)`
  - Declares `PUT /todo/{todo_id}`. `TodoUpdate` fields are optional. `todo.model_dump(exclude_unset=True)` ensures only provided fields are sent to the service.

26-27. `@router.delete("/{todo_id}")` and `delete_todo(...)`
  - Declares `DELETE /todo/{todo_id}` for removing a todo belonging to the user.

Beginner tips:
- Use the Swagger UI at `/docs` to interactively test these endpoints. Remember to authorize using a valid token first.
- `model_dump(exclude_unset=True)` is a Pydantic (v2) helper; in Pydantic v1 you would use `dict(exclude_unset=True)`.

---
