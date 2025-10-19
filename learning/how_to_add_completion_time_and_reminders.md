# How to Add Completion Time and Email Reminders to Todos

This guide explains step-by-step how to add a `completion_time` field to todos and implement an email reminder system that alerts users when 90% of the time has elapsed and the todo is still incomplete.

---

## Overview of the Feature

**What we're building:**
- Add a `completion_time` (deadline) field to todos
- Background task that periodically checks todos approaching their deadline
- Email notification when 90% of time has elapsed and todo is not completed
- Prevent duplicate emails for the same todo

**Example scenario:**
- User creates a todo with completion time: "2025-10-25 18:00:00"
- Created at: "2025-10-20 10:00:00"
- Total duration: 5 days, 8 hours (128 hours)
- 90% threshold: ~115 hours after creation
- Email will be sent at: "2025-10-25 09:00:00" (approximately)

---

## Step 1: Update the Todo Schema

**What to change:** Add `completion_time` field to your Pydantic models.

**File:** `src/todo/schema.py`

**Current structure:**
```python
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

**New structure:**
```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class TodoCreate(BaseModel):
    heading: str
    task: str
    completion_time: Optional[datetime] = Field(
        None, 
        description="Deadline for completing the todo"
    )
    
    @validator('completion_time')
    def validate_completion_time(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError('Completion time must be in the future')
        return v

class TodoUpdate(BaseModel):
    heading: Optional[str] = None
    task: Optional[str] = None
    completed: Optional[bool] = None
    completion_time: Optional[datetime] = None
    
    @validator('completion_time')
    def validate_completion_time(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError('Completion time must be in the future')
        return v

class Todo(BaseModel):
    id: Optional[str] = None
    heading: str
    task: str
    completed: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completion_time: Optional[str] = None  # ISO format string for API response
    reminder_sent: Optional[bool] = False  # Track if reminder was sent
```

**Why these changes:**
- `completion_time` is optional so existing todos without deadlines still work
- Validator ensures users can't set deadlines in the past
- `reminder_sent` flag prevents sending duplicate emails

---

## Step 2: Update the Database Model

**What to change:** Store `completion_time` and `reminder_sent` in MongoDB.

**File:** `src/todo/services/todo.py`

**Update `create_todo_service`:**

```python
def create_todo_service(user_id: str, heading: str, task: str, completion_time: Optional[datetime] = None):
    now = datetime.utcnow()
    new_todo = {
        "user_id": ObjectId(user_id),
        "heading": heading,
        "task": task,
        "completed": False,
        "created_at": now,
        "updated_at": now,
        "completion_time": completion_time,  # NEW: Store deadline
        "reminder_sent": False  # NEW: Track email status
    }
    result = todo_collection.insert_one(new_todo)
    new_todo["_id"] = result.inserted_id
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
```

**Update `get_all_todos_service` and `get_todo_service`:**

Add these fields to the response dictionaries:
```python
"completion_time": t["completion_time"].isoformat() if t.get("completion_time") else None,
"reminder_sent": t.get("reminder_sent", False)
```

**Update `update_todo_service`:**

When a todo is marked as completed, we should not send reminders:
```python
def update_todo_service(user_id: str, todo_id: str, data: dict):
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # If marking as completed, ensure no reminder is sent
    if data.get("completed") == True:
        data["reminder_sent"] = True  # Prevent future reminders
    
    result = todo_collection.update_one(
        {"_id": ObjectId(todo_id), "user_id": ObjectId(user_id)},
        {"$set": {**data, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Todo not found or not authorized")
    return {"msg": "Todo updated successfully"}
```

---

## Step 3: Update the Routes

**What to change:** Accept `completion_time` in create and update endpoints.

**File:** `src/todo/routes/todo.py`

**Update `create_todo` route:**

```python
@router.post("/", response_model=Todo)
def create_todo(todo: TodoCreate, current_user=Depends(get_current_user)):
    return create_todo_service(
        str(current_user["_id"]), 
        todo.heading, 
        todo.task,
        todo.completion_time  # NEW: Pass completion time
    )
```

**Update `update_todo` route:**

No changes needed - `TodoUpdate` already handles optional fields via `model_dump(exclude_unset=True)`.

---

## Step 4: Configure Email Settings

**What to add:** Email credentials and SMTP configuration.

**File:** `.env`

Add email configuration:
```env
# Existing settings...
JWT_SECRET_KEY=ye-meri-key32
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email settings
EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
EMAIL_ENABLED=true
```

**Note for Gmail:**
- Don't use your regular password
- Generate an "App Password" from Google Account settings
- Enable 2-factor authentication first
- Go to: https://myaccount.google.com/apppasswords

**File:** `src/config.py`

Add email settings to configuration:
```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Email settings
    email_sender: str = Field(..., env="EMAIL_SENDER")
    email_password: str = Field(..., env="EMAIL_PASSWORD")
    smtp_host: str = Field("smtp.gmail.com", env="SMTP_HOST")
    smtp_port: int = Field(587, env="SMTP_PORT")
    email_enabled: bool = Field(True, env="EMAIL_ENABLED")
```

---

## Step 5: Create Email Utility

**What to create:** Utility functions for sending emails.

**New file:** `src/utils/email.py`

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config import settings
from src.utils.logger import logger

log = logger()


def send_email(to_email: str, subject: str, body: str, html_body: str = None):
    """
    Send an email using SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text email body
        html_body: Optional HTML version of the body
    """
    if not settings.email_enabled:
        log.info(f"Email disabled. Would send to {to_email}: {subject}")
        return
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = settings.email_sender
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add plain text and HTML parts
        msg.attach(MIMEText(body, 'plain'))
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))
        
        # Connect to SMTP server
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
        server.starttls()
        server.login(settings.email_sender, settings.email_password)
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        log.info(f"Email sent to {to_email}: {subject}")
        
    except Exception as e:
        log.error(f"Failed to send email to {to_email}: {e}")
        raise


def send_todo_reminder(user_email: str, user_name: str, todo_heading: str, 
                       todo_task: str, completion_time: str):
    """
    Send a reminder email about an approaching todo deadline.
    
    Args:
        user_email: User's email address
        user_name: User's name
        todo_heading: Todo heading
        todo_task: Todo task description
        completion_time: Deadline timestamp (formatted)
    """
    subject = f"⏰ Reminder: '{todo_heading}' deadline approaching!"
    
    body = f"""
Hi {user_name},

This is a reminder that your todo is approaching its deadline:

📋 Todo: {todo_heading}
📝 Task: {todo_task}
⏰ Deadline: {completion_time}

You have approximately 10% of the time remaining. Please complete this task soon!

Best regards,
Your Todo App
    """
    
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #e74c3c;">⏰ Todo Deadline Reminder</h2>
        <p>Hi <strong>{user_name}</strong>,</p>
        <p>This is a reminder that your todo is approaching its deadline:</p>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #e74c3c; margin: 20px 0;">
          <p style="margin: 5px 0;"><strong>📋 Todo:</strong> {todo_heading}</p>
          <p style="margin: 5px 0;"><strong>📝 Task:</strong> {todo_task}</p>
          <p style="margin: 5px 0;"><strong>⏰ Deadline:</strong> {completion_time}</p>
        </div>
        
        <p style="color: #e74c3c;"><strong>⚠️ You have approximately 10% of the time remaining!</strong></p>
        <p>Please complete this task soon.</p>
        
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
        <p style="color: #777; font-size: 0.9em;">Best regards,<br>Your Todo App</p>
      </body>
    </html>
    """
    
    send_email(user_email, subject, body, html_body)
```

---

## Step 6: Create Background Reminder Task

**What to create:** A background task that periodically checks for todos needing reminders.

**New file:** `src/utils/reminder_scheduler.py`

```python
import schedule
import time
import threading
from datetime import datetime
from src.utils.db import db, user_collection
from src.utils.email import send_todo_reminder
from src.utils.logger import logger
from bson import ObjectId

log = logger()
todo_collection = db["todos"]


def check_and_send_reminders():
    """
    Check all todos and send reminders for those at 90% completion time.
    """
    log.info("Running reminder check...")
    
    try:
        now = datetime.utcnow()
        
        # Find todos that:
        # 1. Have a completion_time set
        # 2. Are not completed
        # 3. Haven't had a reminder sent yet
        # 4. Are past the 90% threshold
        
        todos = todo_collection.find({
            "completed": False,
            "reminder_sent": False,
            "completion_time": {"$ne": None, "$exists": True}
        })
        
        reminders_sent = 0
        
        for todo in todos:
            completion_time = todo.get("completion_time")
            created_at = todo.get("created_at")
            
            if not completion_time or not created_at:
                continue
            
            # Calculate total duration and 90% threshold
            total_duration = (completion_time - created_at).total_seconds()
            threshold_time = created_at.total_seconds() + (total_duration * 0.9)
            current_time = now.timestamp()
            
            # Check if we're past 90% but before deadline
            if current_time >= threshold_time and current_time < completion_time.timestamp():
                # Get user details
                user = user_collection.find_one({"_id": todo["user_id"]})
                
                if user and user.get("email"):
                    try:
                        # Send reminder email
                        send_todo_reminder(
                            user_email=user["email"],
                            user_name=user.get("name", "User"),
                            todo_heading=todo["heading"],
                            todo_task=todo["task"],
                            completion_time=completion_time.strftime("%Y-%m-%d %H:%M:%S")
                        )
                        
                        # Mark reminder as sent
                        todo_collection.update_one(
                            {"_id": todo["_id"]},
                            {"$set": {"reminder_sent": True}}
                        )
                        
                        reminders_sent += 1
                        log.info(f"Sent reminder for todo {todo['_id']} to {user['email']}")
                        
                    except Exception as e:
                        log.error(f"Failed to send reminder for todo {todo['_id']}: {e}")
        
        log.info(f"Reminder check complete. Sent {reminders_sent} reminders.")
        
    except Exception as e:
        log.error(f"Error in reminder check: {e}")


def run_scheduler():
    """
    Run the scheduler in a background thread.
    """
    # Schedule the task to run every 30 minutes
    schedule.every(30).minutes.do(check_and_send_reminders)
    
    # Alternative schedules:
    # schedule.every(1).hour.do(check_and_send_reminders)  # Every hour
    # schedule.every().day.at("09:00").do(check_and_send_reminders)  # Daily at 9 AM
    
    log.info("Reminder scheduler started")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


def start_reminder_scheduler():
    """
    Start the reminder scheduler in a background thread.
    """
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    log.info("Reminder scheduler thread started")
```

**Alternative: Use APScheduler (More Robust)**

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = BackgroundScheduler()

def start_reminder_scheduler():
    """
    Start the reminder scheduler using APScheduler.
    """
    scheduler.add_job(
        check_and_send_reminders,
        trigger=IntervalTrigger(minutes=30),
        id='todo_reminder_check',
        name='Check and send todo reminders',
        replace_existing=True
    )
    scheduler.start()
    log.info("APScheduler started for reminders")
```

---

## Step 7: Integrate Scheduler with FastAPI

**What to change:** Start the background scheduler when the app starts.

**File:** `src/main.py`

```python
import time
from typing import Any, Callable, TypeVar, Dict
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.utils.logger import logger
from src.auth.routes.auth import router as auth_router
from src.todo.routes.todo import router as todo_router
from src.utils.reminder_scheduler import start_reminder_scheduler  # NEW

description = """
TODO API
"""

log = logger()

app = FastAPI(
    title="TODO API",
    description=description,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    root_path=settings.root_path,
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=["*"],
)


# NEW: Start reminder scheduler on app startup
@app.on_event("startup")
async def startup_event():
    log.info("Starting Todo API...")
    start_reminder_scheduler()
    log.info("Reminder scheduler initialized")


@app.on_event("shutdown")
async def shutdown_event():
    log.info("Shutting down Todo API...")
    # Add cleanup if needed (e.g., scheduler.shutdown())


@app.get("/", tags=["Health"])
async def health_check() -> Dict[str, str]:
    return {"status": "ok", "message": "Todo API is running"}


app.include_router(auth_router)
app.include_router(todo_router)


F = TypeVar("F", bound=Callable[..., Any])


@app.middleware("http")
async def process_time_log_middleware(
    request: Request, call_next: Callable[[Request], Any]
) -> Response:
    start_time = time.time()
    response: Response = await call_next(request)
    process_time = str(round(time.time() - start_time, 3))
    response.headers["X-Process-Time"] = process_time
    log.info(
        "Method=%s Path=%s StatusCode=%s ProcessTime=%s",
        request.method,
        request.url.path,
        response.status_code,
        process_time,
    )
    return response


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        reload=True,
    )
```

---

## Step 8: Install Required Dependencies

**What to add:** Email and scheduling libraries.

**File:** `requirements.txt`

Add these packages:
```txt
# Existing packages...
fastapi
uvicorn
pymongo
pydantic
pydantic-settings
passlib[argon2]
PyJWT
python-multipart

# NEW: For email and scheduling
schedule==1.2.0
# OR use APScheduler (more features):
# apscheduler==3.10.4
```

Install:
```bash
pip install schedule
# or
pip install apscheduler
```

---

## Step 9: Testing the Feature

### Manual Testing Steps

1. **Create a todo with completion time:**
```bash
curl -X POST "http://localhost:8000/todo/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "heading": "Submit report",
    "task": "Complete quarterly report",
    "completion_time": "2025-10-25T18:00:00Z"
  }'
```

2. **Check the response includes completion_time:**
```json
{
  "id": "...",
  "heading": "Submit report",
  "task": "Complete quarterly report",
  "completed": false,
  "created_at": "2025-10-20T10:00:00",
  "updated_at": "2025-10-20T10:00:00",
  "completion_time": "2025-10-25T18:00:00",
  "reminder_sent": false
}
```

3. **Simulate time passing (for testing):**

Temporarily modify `check_and_send_reminders` to use a smaller threshold:
```python
# For testing: use 10% instead of 90%
threshold_time = created_at.total_seconds() + (total_duration * 0.1)
```

Or manually update the MongoDB document:
```javascript
db.todos.updateOne(
  {_id: ObjectId("...")},
  {$set: {created_at: new Date("2025-10-15T10:00:00Z")}}
)
```

4. **Trigger reminder manually:**
```python
# Create test script: test_reminder.py
from src.utils.reminder_scheduler import check_and_send_reminders

check_and_send_reminders()
```

5. **Verify email received and database updated:**
```javascript
// Check in MongoDB
db.todos.find({reminder_sent: true})
```

---

## Step 10: Monitoring and Logging

### Add Logging to Track Reminders

**File:** `src/utils/reminder_scheduler.py`

Already includes logging. Monitor logs:
```bash
# Watch logs in real-time
tail -f logs/app.log

# Or check uvicorn output
# Look for:
# "Running reminder check..."
# "Sent reminder for todo ... to user@email.com"
# "Reminder check complete. Sent X reminders."
```

### Add Health Check for Scheduler

**File:** `src/main.py`

```python
from src.utils.reminder_scheduler import scheduler  # if using APScheduler

@app.get("/health/scheduler")
async def scheduler_health():
    if scheduler.running:
        return {
            "status": "ok",
            "jobs": len(scheduler.get_jobs()),
            "next_run": str(scheduler.get_jobs()[0].next_run_time) if scheduler.get_jobs() else None
        }
    return {"status": "not running"}
```

---

## Step 11: Production Considerations

### 1. Use a Task Queue (Celery + Redis/RabbitMQ)

For production, replace the threading scheduler with Celery:

**Why:** 
- Better error handling
- Retries on failure
- Distributed task execution
- Monitoring with Flower

**Setup:**
```bash
pip install celery redis
```

**File:** `src/celery_app.py`
```python
from celery import Celery
from src.config import settings

celery_app = Celery(
    'tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

celery_app.conf.beat_schedule = {
    'check-reminders-every-30-minutes': {
        'task': 'src.tasks.check_reminders',
        'schedule': 1800.0,  # 30 minutes
    },
}

celery_app.conf.timezone = 'UTC'
```

**File:** `src/tasks.py`
```python
from src.celery_app import celery_app
from src.utils.reminder_scheduler import check_and_send_reminders

@celery_app.task
def check_reminders():
    check_and_send_reminders()
```

**Run Celery worker and beat:**
```bash
celery -A src.celery_app worker --loglevel=info
celery -A src.celery_app beat --loglevel=info
```

### 2. Add Database Index

Create an index for faster queries:

```python
# Add to src/utils/db.py or run in mongo shell
todo_collection.create_index([
    ("completed", 1),
    ("reminder_sent", 1),
    ("completion_time", 1)
])
```

### 3. Handle Email Failures Gracefully

Add retry logic:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def send_email_with_retry(to_email, subject, body, html_body=None):
    send_email(to_email, subject, body, html_body)
```

### 4. Add Email Templates

Use Jinja2 for better email templates:

```bash
pip install jinja2
```

**File:** `templates/reminder_email.html`
```html
<!DOCTYPE html>
<html>
<head>
    <style>
        /* CSS styles */
    </style>
</head>
<body>
    <h2>⏰ Todo Deadline Reminder</h2>
    <p>Hi <strong>{{ user_name }}</strong>,</p>
    <!-- Template content -->
</body>
</html>
```

### 5. Add User Preferences

Allow users to opt out of reminders:

**Update user schema:**
```python
# In user registration/profile
{
    "email_notifications": True,
    "reminder_threshold": 0.9  # 90%, but user can customize
}
```

**Check preferences before sending:**
```python
if user.get("email_notifications", True):
    send_reminder(...)
```

---

## Common Issues and Troubleshooting

### Issue 1: Emails Not Sending

**Symptoms:** No errors but emails don't arrive

**Solutions:**
1. Check spam folder
2. Verify SMTP credentials in `.env`
3. For Gmail: ensure App Password is used (not regular password)
4. Check firewall/network allows SMTP port 587
5. Test with a simple script:
   ```python
   from src.utils.email import send_email
   send_email("your-email@example.com", "Test", "Testing email setup")
   ```

### Issue 2: Scheduler Not Running

**Symptoms:** Logs don't show "Running reminder check..."

**Solutions:**
1. Check startup logs for scheduler initialization
2. Ensure `@app.on_event("startup")` is called
3. If using `--reload`, scheduler might restart frequently (disable in prod)
4. Check thread is alive:
   ```python
   import threading
   print(threading.active_count())  # Should be > 1
   ```

### Issue 3: Wrong Time Calculations

**Symptoms:** Reminders sent too early or too late

**Solutions:**
1. Ensure all datetime objects use UTC (`datetime.utcnow()`)
2. Verify completion_time is stored as datetime, not string
3. Add logging to show calculated thresholds:
   ```python
   log.info(f"Created: {created_at}, Completion: {completion_time}, Threshold: {threshold_time}")
   ```

### Issue 4: Duplicate Reminders

**Symptoms:** Users receive multiple emails for same todo

**Solutions:**
1. Ensure `reminder_sent` flag is set atomically
2. Add unique constraint or check before sending:
   ```python
   result = todo_collection.find_one_and_update(
       {"_id": todo["_id"], "reminder_sent": False},
       {"$set": {"reminder_sent": True}},
       return_document=True
   )
   if result:  # Only send if update succeeded
       send_email(...)
   ```

---

## Advanced Enhancements

### 1. Multiple Reminder Levels

Send reminders at 50%, 75%, 90%, and 95%:

```python
REMINDER_THRESHOLDS = [0.5, 0.75, 0.9, 0.95]

# Store in todo:
"reminders_sent": []  # List of thresholds already sent

# Check each threshold:
for threshold in REMINDER_THRESHOLDS:
    if threshold not in todo["reminders_sent"]:
        # Send and update
```

### 2. Customizable Reminder Times

Let users choose when to get reminders:

```python
class TodoCreate(BaseModel):
    # ...
    reminder_thresholds: Optional[List[float]] = [0.9]  # Default 90%
```

### 3. Different Notification Channels

Add SMS, Push notifications, Slack, etc.:

```python
# src/utils/notifications.py
def send_notification(user, message, channels=['email']):
    if 'email' in channels and user.get('email'):
        send_email(...)
    if 'sms' in channels and user.get('phone'):
        send_sms(...)
    if 'push' in channels:
        send_push_notification(...)
```

### 4. Snooze Feature

Allow users to snooze reminders:

```python
# Add endpoint
@router.post("/todo/{todo_id}/snooze")
def snooze_reminder(todo_id: str, minutes: int = 60):
    # Reset reminder_sent and adjust threshold
```

---

## Testing Checklist

Before deploying to production:

- [ ] Test creating todo with completion_time
- [ ] Test creating todo without completion_time (backward compatibility)
- [ ] Test updating completion_time
- [ ] Test marking todo as completed stops reminders
- [ ] Test email delivery (check inbox and spam)
- [ ] Test scheduler runs on app startup
- [ ] Test 90% threshold calculation is correct
- [ ] Test reminder_sent flag prevents duplicates
- [ ] Test with multiple users and todos
- [ ] Test email template renders correctly (HTML and plain text)
- [ ] Load test: 1000+ todos with completion times
- [ ] Test timezone handling (if supporting multiple timezones)

---

## Summary

To add completion time and email reminders:

1. ✅ Update schemas with `completion_time` field
2. ✅ Update database models to store deadline and reminder status
3. ✅ Configure email settings in `.env`
4. ✅ Create email utility functions
5. ✅ Create background task to check todos
6. ✅ Integrate scheduler with FastAPI startup
7. ✅ Test the feature thoroughly
8. ✅ Consider production setup (Celery, monitoring)

This feature significantly enhances the todo app by helping users stay on top of deadlines!
