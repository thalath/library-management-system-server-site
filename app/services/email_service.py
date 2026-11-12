import os
import smtplib
from email.message import EmailMessage
from typing import List, Optional

from flask import current_app

from extensions import db
from app.utils.otp import hash_otp
from app.models.user import User
from app.models.email_otp import EmailOTP
from datetime import datetime, timedelta


class EmailOTPService:

    @staticmethod
    def get_all_email_otp() -> List[EmailOTP]:
        return EmailOTP.query.order_by(EmailOTP.id.desc()).all()

    def get_email_otp_by_id(otp_id: int) -> Optional[EmailOTP]:
        return db.session.get(EmailOTP, otp_id)
    
    @staticmethod
    def create_email_otp(data: dict, user_id: Optional[int] = None, otp: Optional[str] = None) -> EmailOTP:
        email_otp = EmailOTP(
            expired_at = data.get('expired_at', datetime.utcnow() + timedelta(minutes=5)),
            is_used = data.get('is_used', False),
            attempts = data.get('attemps', 0),
            purpose = data['purpose']
        )

        if otp:
            email_otp.otp_hash = hash_otp(otp)
        
        if user_id:
            user = db.session.get(User, user_id)
            if user:
                email_otp.user = user
                email_otp.user_id = user.id

        db.session.add(email_otp)
        db.session.commit()
        return email_otp

    @staticmethod
    def update_email_otp(email_otp: EmailOTP, data: dict, user_id: Optional[int] = None) -> EmailOTP:
        email_otp.otp_hash = data.get("otp", email_otp.otp_hash)
        email_otp.is_used = data.get("is_used", email_otp.is_used)
        email_otp.attempts = data.get("attempts", email_otp.attempts)
        email_otp.purpose = data.get("purpose", email_otp.purpose)
        if user_id:
            user = db.session.get(User, user_id)
            if user:
                email_otp.user_id = data.get("user_id", email_otp.user_id)
        db.session.commit()
        return email_otp


    # ================== Send OTP to email =======================
    @staticmethod
    def send_otp_email(receiver_email, full_name, otp):
        sender_email = current_app.config["MAIL_USERNAME"]
        sender_password = current_app.config["MAIL_PASSWORD"]

        message = EmailMessage()

        message["Subject"] = "Library Management system - Email verification"
        message["from"] = sender_email
        message["To"] = receiver_email
        message.set_content(
            f"""
Hello, {full_name}!

Thank you for registering with our Library Management System.

Your verification code is:

{otp}

This code expired in 5 minutes.

if you did not request this code, Please ignore this email.

Thank you.

Library Management System
            """
        )

        try:
            with smtplib.SMTP(
                current_app.config["MAIL_SERVER"],
                current_app.config["MAIL_PORT"],
                timeout=20
            ) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()

                server.login(sender_email, sender_password)
                server.send_message(message)

            return True

        except (smtplib.SMTPException, OSError):
            current_app.logger.exception("Failed to send OTP email.")
            return False
