import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_email(to_email: str, subject: str, body: str):
    """Sends an email using Resend API."""
    # Load Resend configuration
    resend_key = os.getenv("RESEND_API_KEY")
    sender = os.getenv("SENDER_EMAIL")

    if not resend_key or not sender:
        return {"error": "Resend API credentials not configured in .env"}

    try:
        from resend import Resend
        client = Resend(resend_key)
        # Resend expects HTML; wrap plain body in <p>
        response = client.emails.send({
            "from": sender,
            "to": [to_email],
            "subject": subject,
            "html": f"<p>{body}</p>"
        })
        # The response may contain an 'id' on success or an 'error' dict
        if isinstance(response, dict) and response.get("error"):
            return {"status": "error", "message": response["error"]["message"]}
        return {"status": "success", "message": f"Email sent to {to_email}"}
    except Exception as e:
        return {"status": "error", "message": f"Resend email failed: {str(e)}"}

def create_ticket(title: str, description: str):
    ticket_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tickets.txt")
    ticket_content = f"--- NEW TICKET ---\nTitle: {title}\nDescription: {description}\n------------------\n\n"

    try:
        with open(ticket_log, "a") as f:
            f.write(ticket_content)
        return {"status": "success", "message": f"Ticket '{title}' created."}
    except Exception as e:
        return {"status": "error", "message": str(e)}