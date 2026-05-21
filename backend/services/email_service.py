import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.config import get_settings
from backend.utils.logger import app_logger

settings = get_settings()

def send_otp_email(recipient_email: str, otp_code: str) -> bool:
    """
    Sends an OTP code using Gmail SMTP.
    Returns True if successful, False otherwise.
    """
    sender_email = settings.smtp_email
    sender_password = settings.smtp_password

    if not sender_email or not sender_password:
        app_logger.error("SMTP credentials are not configured. Cannot send OTP email.")
        # We can still return True in development if we want to bypass, but for production we return False.
        return False

    subject = "Your CravingAI OTP Code"
    body = f"""Your OTP code is: {otp_code}

This code will expire in 10 minutes.
Do not share it with anyone.
"""

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Secure the connection
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        app_logger.info(f"Successfully sent OTP to {recipient_email}")
        return True
    except Exception as e:
        app_logger.error(f"Failed to send email to {recipient_email}: {e}")
        return False
