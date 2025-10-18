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
