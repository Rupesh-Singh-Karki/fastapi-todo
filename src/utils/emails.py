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