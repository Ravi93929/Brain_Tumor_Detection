import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config


def send_email(receiver_email, subject, body):
    print("=== SEND_EMAIL CALLED ===")
    print(f"DEBUG_OTP_MODE: {Config.DEBUG_OTP_MODE}")
    print(f"MAIL_USERNAME: {Config.MAIL_USERNAME}")
    print(f"RECEIVER: {receiver_email}")
    print(f"SUBJECT: {subject}")

    if Config.DEBUG_OTP_MODE:
        raise RuntimeError("DEBUG_OTP_MODE is True. Real email sending is disabled.")

    if not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD:
        raise RuntimeError("MAIL_USERNAME or MAIL_PASSWORD is missing.")

    msg = MIMEMultipart()
    msg["From"] = Config.MAIL_USERNAME
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
    server.sendmail(Config.MAIL_USERNAME, receiver_email, msg.as_string())
    server.quit()

    print("=== EMAIL SENT SUCCESSFULLY ===")