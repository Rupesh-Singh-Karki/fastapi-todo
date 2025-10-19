from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime, timezone

class TodoCreate(BaseModel):
    heading: str
    task: str
    completion_time: Optional[datetime] = Field(
        None, description="Deadline for completing the todo"
    )

    @validator("completion_time")
    def validate_completion_time(cls, v):
        if v and v < datetime.now(timezone.utc):
            raise ValueError("completion_time must be in the future")
        return v


class TodoUpdate(BaseModel):
    heading: Optional[str] = None
    task: Optional[str] = None
    completed: Optional[bool] = None
    completion_time: Optional[datetime] = None

    @validator("completion_time")
    def validate_completion_time(cls, v):
        if v and v < datetime.now(timezone.utc):
            raise ValueError("completion_time must be in the future")
        return v


class Todo(BaseModel):
    id: Optional[str] = None
    heading: str
    task: str
    completed: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completion_time: Optional[datetime] = None  # ISO format datetime
    reminder_sent: Optional[bool] = False       # tracking if reminder sent