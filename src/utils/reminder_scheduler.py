import schedule
import time
import threading
from datetime import datetime
from src.utils.db import db, user_collection
from src.utils.emails import send_todo_reminder
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
            threshold_time = created_at.timestamp() + (total_duration * 0.9)
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