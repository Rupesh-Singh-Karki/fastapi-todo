
# `src/todo/schema.py` — Beginner Explanation (Line-by-line)

This file defines the Pydantic models that validate input and format output for the todo endpoints. Below is the code and explanations for each line.

---

Code (complete file):

```python
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
```

Line-by-line explanation:

1. `from pydantic import BaseModel`
  - Pydantic's `BaseModel` is the base class for creating data models that validate input and serialize output.

2. `from typing import Optional`
  - `Optional` indicates that a field may be present or `None`.

3. `from datetime import datetime`
  - Imported for context; in this file we don't store `datetime` objects directly in models, but the services use UTC datetimes.

4-6. `class TodoCreate(BaseModel): ...`
  - `heading` and `task` are required string fields. This model is used for creating todos (POST requests).

7-10. `class TodoUpdate(BaseModel): ...`
  - All fields are optional. This allows partial updates with `exclude_unset=True`.

11-18. `class Todo(BaseModel): ...`
  - This is the response model with fields that the API returns. `id` and timestamps are optional because they are set by the server.

Why split models?
- Input models (`TodoCreate`, `TodoUpdate`) define what the client may send.
- Response model (`Todo`) defines what the API returns. Keeping them separate prevents clients from sending fields like `id` or `created_at` which should be server-owned.

Beginner tip
- If you add `response_model=Todo` in a route, FastAPI will validate the outgoing data—this helps keep your API predictable.

---
