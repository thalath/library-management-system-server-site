import secrets
import hashlib
import hmac

from flask import current_app

def generate_otp():
    """
    GENERATE A RANDOM 6-digits OTP
    """

    return f"{secrets.randbelow(1000000):06d}"

def hash_otp(otp):
    """
    Hash OTP using the application secret_key
    """

    secret = current_app.config["SECRET_KEY"]
    
    return hmac.new(
        secret.encode("utf-8"),
        otp.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

def verify_otp_hash(otp, stored_hash):
    """
    Compare OTP Securely
    """

    generated_hash = hash_otp(otp)

    return hmac.compare_digest(
        generated_hash,
        stored_hash
    )
