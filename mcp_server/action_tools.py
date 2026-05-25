import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_email(to_email: str, subject: str, body: str):
    sender = os.getenv("GMAIL_SENDER")
    password = os.getenv("GMAIL_APP_PASSWORD")

    if not sender or not password:
        return {"error": "Email credentials not configured."}

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender, password)
            server.sendmail(sender, [to_email], msg.as_string())
        return {"status": "success", "message": f"Email sent to {to_email}"}
    except smtplib.SMTPAuthenticationError:
        return {"status": "error", "message": "Auth failed. Check GMAIL_APP_PASSWORD."}
    except smtplib.SMTPException as e:
        return {"status": "error", "message": f"SMTP error: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Network error: {str(e)}"}

def create_ticket(title: str, description: str):
    ticket_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tickets.txt")
    ticket_content = f"--- NEW TICKET ---\nTitle: {title}\nDescription: {description}\n------------------\n\n"

    try:
        with open(ticket_log, "a") as f:
            f.write(ticket_content)
        return {"status": "success", "message": f"Ticket '{title}' created."}
    except Exception as e:
        return {"status": "error", "message": str(e)}