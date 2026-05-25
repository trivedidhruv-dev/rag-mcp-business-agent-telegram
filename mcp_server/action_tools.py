import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

def send_email(to_email: str, subject: str, body: str):
    """Sends an email using Gmail SMTP and App Password."""
    sender = os.getenv("GMAIL_SENDER")
    password = os.getenv("GMAIL_APP_PASSWORD")
    
    if not sender or not password or "your" in sender or "your" in password:
        return {"error": "Email credentials not configured in .env"}

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to_email

    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=10.0) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [to_email], msg.as_string())
        return {"status": "success", "message": f"Email sent successfully to {to_email}"}
    except Exception as e:
        return {"status": "error", "message": f"Network issue or timeout: {str(e)}"}

def create_ticket(title: str, description: str):
    """Simulates ticket creation by logging to a file."""
    ticket_log = os.path.join(os.getcwd(), "tickets.txt")
    ticket_content = f"--- NEW TICKET ---\nTitle: {title}\nDescription: {description}\n------------------\n\n"
    
    try:
        with open(ticket_log, "a") as f:
            f.write(ticket_content)
        return {"status": "success", "message": f"Ticket '{title}' created and logged to tickets.txt"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Test ticket creation
    print(create_ticket("Test Ticket", "This is a test ticket from our agent."))
