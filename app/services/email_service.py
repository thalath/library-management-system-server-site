import smtplib

from email.message import EmailMessage
from flask import current_app

def send_otp_email(receiver_email, otp):
    sender_email = current_app.config["MAIL_USERNAME"]
    sender_password = current_app.config["MAIL_PASSWORD"]

    message = EmailMessage()

    message["Subject"] = "Library Management system - Email verification"
    message["from"] = sender_email
    message["To"] = receiver_email
    message.set_content(
        f"""
Hello,

Thank you for registering with our Library Management System.

Your verification code is:

{otp}

This code expired in 5 minutes.

if you did not request this code, Please ignore this emaail.

Thank you.

Library Management System
"""
    )

    try:
        with smtplib.SMTP(
            current_app.config["MAIL_SERVER"],
            current_app.config["MAIL_PORT"]
        ) as server:
            server.starttls()

            server.login(
                sender_email,
                sender_password
            )
            server.send_message(message)
        return True

    except Exception:
        current_app.logger.exception("Failed to send OTP email.")
        return False
