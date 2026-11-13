import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from typing import List, Optional

from flask import current_app

from extensions import db
from app.models.email_otp import EmailOTP
from app.utils.otp import hash_otp, verify_otp_hash
from app.repositories.user_repository import get_user_by_id


class EmailOTPService:

    @staticmethod
    def get_all_email_otp() -> List[EmailOTP]:
        return EmailOTP.query.order_by(EmailOTP.id.desc()).all()

    def get_email_otp_by_id(otp_id: int) -> Optional[EmailOTP]:
        return db.session.get(EmailOTP, otp_id)
    
    @staticmethod
    def create_otp(
        purpose: Optional[str] = "email_verification", 
        user_id: Optional[int] = None, 
        otp: Optional[str] = None,
        minutes=10
    ) -> Optional[EmailOTP]:
        email_otp = EmailOTP(
            purpose = purpose,
            expired_at = datetime.utcnow() + timedelta(minutes=minutes),
            attempts = 0,
            is_used = False,
        )
        
        if user_id:
            user = get_user_by_id(user_id)
            if user:
                email_otp.user_id = user_id
        if otp:
            email_otp.otp_hash = hash_otp(otp)
            
        db.session.add(email_otp)
        db.session.commit()
        return email_otp

    @staticmethod
    def verify(user_id: int, otp: str, purpose: str) -> Optional[EmailOTP]:
        verification = EmailOTP.query.filter_by(
            user_id=user_id,
            purpose=purpose,
            is_used=False
        ).order_by(
            EmailOTP.created_at.desc()
        ).first()
        
        if not verification:
            return None
        
        if verification.expired_at < datetime.utcnow():
            return None
        
        if verification.attempts >= 5:
            return None
        
        if not verify_otp_hash(otp, verification.otp_hash):
            verification.attempts += 1
            db.session.commit()
            
            return None

        verification.is_used = True
        
        db.session.commit()

        return verification


    # ================== Send OTP to email =======================
    @staticmethod
    def send_otp(receiver_email, full_name, otp):
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
