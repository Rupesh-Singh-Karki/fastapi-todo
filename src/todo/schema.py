from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TodoCreate(BaseModel):
    heading: str
    task: str

class TodoUpdate(BaseModel):
    heading: Optional[str] = None
    task: Optional[str] = None
    completed: Optional[bool] = None

class Todo(BaseModel):
    id: Optional[str] = None
    heading: str
    task: str
    completed: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
