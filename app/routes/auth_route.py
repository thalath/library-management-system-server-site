from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import (jwt_required, create_access_token, 
                                create_refresh_token, get_jwt_identity,
                                decode_token, get_jwt, set_access_cookies,
                                set_refresh_cookies, unset_jwt_cookies)

from app.services.user_service import UserService
from app.services.email_service import send_otp_email
from app.models.user import User
from app.models.token_blocklist import TokenBlocklist
from app.models.role import Role
from extensions import db
import re
from app.utils import otp
from datetime import datetime, timedelta
from app.models.email_otp import EmailOTP


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/login")
def login():
    data = request.get_json()
    if not data:
        return jsonify({
            "msg": "Invalid or Missing email and password",
            "status": 404
        }), 404

    email = data.get("email", "").strip()
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):
        if not user.is_active:
            return jsonify({
                "msg": "You account is Inactive, Please Contact admin to activate first",
                "status": 403
            }), 403
            
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        response = jsonify({"msg": "Login successfully."})
        
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        
        return response, 200

    return jsonify({
        "msg": "Invalid Email or Password",
        "status": 401
    }), 401


@auth_bp.post("/register")
def register():
    data = request.get_json()
    if not data:
        return jsonify({
            "msg": "Invalid or Missing JSON payload",
            "status": 400
        }), 400

    username = data.get("username", "").strip()
    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    confirmation_password = data.get("confirmation_password", "").strip()

    errors: list[str] = []

    if not username:
        errors.append("Username is required.")
    if not full_name:
        errors.append("Full Name is required.")

    if not email:
        errors.append("Email is required.")
    if not password:
        errors.append("Strong password is required.")

    if password:
        if len(password) < 8:
            errors.append("Password must be contained at least 8 characters.")
        if not re.search(r"[a-z]", password):
            errors.append("Password must contained at least one lowercase character.")
        if not re.search(r"[A-Z]", password):
            errors.append("Password must contained at least one uppercase character.")
        if not re.search(r"[0-9]", password):
            errors.append("Password must contained at least one digit number")
        if not re.search(r"[!@#$%^&*()_+=-~`{}|:';,./?><]", password):
            errors.append("Password must contained at least one special character.")
        if password != confirmation_password:
            errors.append("Confirm Password must matched.")

    email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
    if email and not re.match(email_pattern, email):
        errors.append("Invalid Email format.")

    if username:
        exists_username = User.query.filter_by(username=username).first()
        if exists_username:
            errors.append("Username is already taken")


    if email:
        exists_email = User.query.filter_by(email=email).first()
        if exists_email:
            errors.append("Email is already registered.")

    if errors:
        return jsonify({
            "msg": "Invalid or Missing Fields.",
            "errors": errors,
            "status": 400
        }), 400

    try:
        safe_user = {
            "username": username,
            "full_name": full_name,
            "email": email,
            "is_active": data.get("is_active", True)
        }

        default_role = Role.query.filter_by(name="User").first()
        default_role_id = default_role.id if default_role else None
        
        new_user = UserService.create(safe_user, password, default_role_id)

        if new_user:
            g_otp = otp.generate_otp()
            otp_record = EmailOTP(
                user_id = new_user.id,
                otp_hash = otp.hash_otp(g_otp),
                purpose = "email_verification",
                expired_at = datetime.utcnow() + timedelta(minutes=5),
                attempts=0,
                is_used = False
            )

            db.session.add(otp_record)
            db.session.commit()


        access_token = create_access_token(identity=str(new_user.id))
        refresh_token = create_refresh_token(identity=str(new_user.id))

        response = jsonify({"msg": "Registered successfully"})
            
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        email_send = send_otp_email(email, full_name, g_otp)
        if not email_send:
            return jsonify({
                "msg": "Your created successfully, but we could not send OTP. Please request a new code.",
                "email": email
            }), 503
        
        # return response, 201

        return jsonify({
            "msg": "Regitration successfully. Please check you email for OTP.",
            "email": email
        }), 201
    except Exception as e:
        db.session.rollback()
                
        return jsonify({
            "msg": "Registration Failed, Please try again.",
            "error": str(e)
        }), 500




@auth_bp.post("/verify-otp")
@jwt_required()
def verify_otp():
    data = request.get_json()
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not data:
        jsonify({
            "msg": "JSON body is required.",
            "error": 400
        }), 400

    otp = data.get("otp", "").strip()

    try:
        
        if user.is_verified:
            return jsonify({
                "msg": "This email is already verified.",
            }), 409


        otp_record = (
            EmailOTP.query.filter_by(
                user_id = user.id,
                purpose="email_verification",
                is_used = False
            )
        ).order_by(EmailOTP.created_at.desc()).first()
        
        
        if not otp_record.attempts >= 5:
            otp_record.is_used = True
            db.session.commit()

            return jsonify({
                "msg": "Maximum attempts reached. Please request a new OTP."
            }), 429

        if not otp.verifiy_otp_hash(otp, otp_record.otp_hash):
            otp_record.attempts += 1

            if otp_record.attempts >= 5:
                otp_record.is_used = True

            db.session.commit()
            
            return jsonify({
                "msg": "Incorrect OTP.",
                "remaining_attempts": max(0, 5 - otp_record.attempts)
            }), 400

        otp_record.is_used = True
        user.is_verified = True
        (
            EmailOTP.query
            .filter(
                EmailOTP.user_id == user.id,
                EmailOTP.purpose == "email_verification",
                EmailOTP.is_used._is(False),
                EmailOTP.id != otp_record.id
            )
            .update(
                {EmailOTP.is_used: True},
                synchronize_session=False
            )
        )

        db.session.commit()

        return jsonify({
            "msg": "Email verified successfully. You can now log in.",
            "email": user.email,
            "is_verified": user.is_verified
        }), 200

    except Exception as e:
        print(f"Testing1: {str(e)}")
        db.session.rollback()
        current_app.logger.exception("OTP verification failed.")
        return jsonify({"msg": "Something went wrong. Please try again."}), 500

    
@auth_bp.post("/send-otp")
@jwt_required()
def send_otp():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    receiver_email, name = user.email, user.full_name
    create_otp = otp.generate_otp()

    success = send_otp_email(receiver_email, name, create_otp)
    if not success:
        jsonify({"error": "Unable to send verification email. Please try again."}), 503

    return jsonify({"msg": "OTP send successfully."}), 200
    




@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=str(current_user_id))
    response = jsonify({
        "msg": "Refresh successfully",
        "access_token": new_access_token
    })
    
    set_access_cookies(response, new_access_token)
    
    return response, 200

@auth_bp.post("/logout")
@jwt_required()
def logout():
    jwt_data = get_jwt()
    jti = jwt_data['jti']
    db.session.add(TokenBlocklist(jti=jti, type="access"))

    cookie_name = current_app.config.get("JWT_REFRESH_COOKIE_NAME", 'refresh_token')
    refresh_token_string = request.cookies.get(cookie_name)

    if refresh_token_string:
        try:
            decoded_refresh = decode_token(refresh_token_string)
            if decoded_refresh.get("type") == "refresh":
                refresh_jti = decoded_refresh["jti"]
                db.session.add(TokenBlocklist(jti=refresh_jti, type="refresh"))
        except Exception:
            pass
    db.session.commit()
    response = jsonify({"msg": "Successful logged out of all sessions."})
    unset_jwt_cookies(response)
    
    return response, 200
