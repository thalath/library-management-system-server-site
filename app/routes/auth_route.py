import re
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import (jwt_required, create_access_token, 
                                create_refresh_token, get_jwt_identity,
                                decode_token, get_jwt, set_access_cookies,
                                set_refresh_cookies, unset_jwt_cookies)
from marshmallow import ValidationError

from extensions import db
from app.services.user_service import UserService
from app.services.email_service import EmailOTPService
from app.models.user import User
from app.models.role import Role
from app.models.email_otp import EmailOTP
from app.models.token_blocklist import TokenBlocklist
from app.schemas.auth_schema import LoginSchema
from app.repositories.user_repository import filter_user_by_email
from app.utils.otp import generate_otp, verify_otp_hash


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/email_verification")
@jwt_required()
def email_verification():
    data = request.get_json()
    if not data:
        return jsonify({
            "msg": "JSON payload is required.",
            "error": str(data)
        }), 400

    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    otp = data['otp']
    purpose = data['purpose']

    errors = []

    if not otp:
        errors.append('OTP is Required.')

    if not purpose:
        errors.append('The OTP verification is must contained with Purpose.')

    if errors:
        return jsonify({
            "msg": "Invalid or Missing JSON payload.",
            "errors": str(errors[0])
        }), 400

    try:
        email_otp = EmailOTPService.create_email_otp(data, user_id)

        return jsonify({
            "msg": "EmailOTP created successfully.",
            "data": email_otp.to_dict()
        }), 201

    except Exception as e:

        return jsonify({
            "msg": "EmailOTP created Failed. Please try again later.",
            "errors": str(e)
        }), 500
    
@auth_bp.post("/login")
def login():
    schema = LoginSchema()
    
    try:
        data = schema.load(
            request.get_json(silent=True) or {}
        )

        user = filter_user_by_email(data['email'])
        
        if not user or not user.check_password(data['password']):
            return jsonify({
                "message": "Invalid Email or Password",
                "status": 401
            }), 401
            
        if not user.is_active:
            return jsonify({
                "message": "You account is inactive, Please contact an administrator.",
                "status": 403
            }), 403
                
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        response = jsonify({
            "message": "Login successfully.",
            "status": 200
        })
            
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
            
        return response, 200
    
    except ValidationError as v_e:
        return jsonify({
            "message": "Validation Failed, Please check error and try again.",
            "errors": v_e.messages,
            "status": 422
        }), 422


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

        access_token = create_access_token(identity=str(new_user.id))
        refresh_token = create_refresh_token(identity=str(new_user.id))

        response = jsonify({"msg": "Registered successfully"})
            
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        
        otp = generate_otp()
        EmailOTPService.send_otp_email(email, full_name, otp)

        data = {
            "purpose": "email_verification",
            "expired_at": datetime.utcnow() + timedelta(minutes=5),
            "otp": otp,
        }

        EmailOTPService.create_email_otp(data, new_user.id)
        return response, 201

    except Exception as e:
        db.session.rollback()
                
        return jsonify({
            "msg": "Registration Failed, Please try again.",
            "error": str(e)
        }), 500


@auth_bp.post("/forgot-password")
def forgot_password():
    data = request.get_json()
   
    if not data:
        return jsonify({
            "msg": "JSON payload is required.",
            "status": "error"
        }), 400

    email = data.get("email", "").strip()
    
    if not email:
        return jsonify({
            "msg": "JSON payload is required."
        }), 400

    otp = generate_otp()

    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                "msg": "Your email is incorrect. Please try again."
            }), 400

        new_otp_data = {
            "purpose": "password_reset",
            "otp": otp,
            "expired_at": datetime.utcnow() + timedelta(minutes=5)
        }

        email_otp = EmailOTPService.create_email_otp(new_otp_data, user.id)
        EmailOTPService.send_otp_email(user.email, user.full_name, otp)
        return jsonify({
            "msg": "Reset Password OTP has been sent please check your email verification.",
            "status": "success",
            "Info": email_otp.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Cannot send OTP to Email")

        return jsonify({
            "msg": "Internal Error accured.",
            "errors": str(e)
        }), 500

@auth_bp.post("/verify-reset-otp")
def verifying_password():
    data = request.get_json()
    if not data:
        return jsonify({
            "msg": "JSON payload is required.",
        }), 400

    otp = data.get("otp", "").strip()
    email = data.get("email", "").strip()

    if not email or not otp:
        return jsonify({
            "msg": "email or otp is required"
        }), 400

    try:
        user = User.query.filter_by(email=email).first()
        otp_record = EmailOTP.query.filter_by(user_id=user.id, purpose="password_reset", is_used=False).order_by(EmailOTP.created_at.desc()).all()
        
        if otp_record:
            if otp_record.attempts >= 5:
                otp.record.is_used = True
                db.session.commit()

            return jsonify({
                "msg": "Maximum attempts reached. Please request a new OTP code."
            }), 429

        current_time = datetime.utcnow()
        if current_time > otp_record.expired_at:
            return jsonify({
                "msg": "OTP is expired. Please request for a new OTP"
            }), 410 # 410 preffered for expired resources.

        if not verify_otp_hash(otp, otp_record.otp_hash):
            otp_record.attempts += 1
            db.session.commit()


            if otp_record.attempts >= 5:
                otp_record.is_used = True
                db.session.commit()

                return jsonify({
                    "msg": "Incorrect OTP.",
                    "remaining": max(0, 5 - otp_record.attempts)
                }), 400

        otp_record.is_used = True
        (
            EmailOTP.query
            .filter(
                EmailOTP.user_id == user.id,
                EmailOTP.purpose == "password_reset",
                EmailOTP.is_used.is_(False),
                EmailOTP.id != otp_record.id
            )
            .update(
                {EmailOTP.is_used: True},
                synchronize_session = False
            )
        )

        db.session.commit()
            
        return jsonify({
            "msg": "Password verification is correct, please go log in.",
            "info": otp_record.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("OTP verification failed.")
        return jsonify({
        "msg": "Internal Error accured.",
        "errors": str(e)
    }), 500

@auth_bp.post("/reset-password")
def reset_password():
    data = request.get_json()
    if not data:
        return jsonify({
            "msg": "JSON payload is required.",
        }), 400

    


@auth_bp.post("/verify-otp")
@jwt_required()
def verify_otp():
    data = request.get_json(silent=True) or {}
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

        otp_id = EmailOTP.query.filter_by(user_id=user_id).first()
        otp_record = EmailOTPService.get_email_otp_by_id(otp_id.id)
        
        if otp_record.attempts >= 5:
            data = {
                "is_used": True
            }

            EmailOTPService.update_email_otp(otp_record, data)

            return jsonify({
                "msg": "Maximum attempts reached. Please request a new OTP.",
                "data": otp_record.to_dict()
            }), 429

        if not verify_otp_hash(otp, otp_record.otp_hash):
            otp_record.attempts += 1
            
            db.session.commit()

            if otp_record.attempts >= 5:
                EmailOTPService.update_email_otp(otp_record, {"is_used": True})
            
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
                EmailOTP.is_used.is_(False),
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
        db.session.rollback()
        current_app.logger.exception("OTP verification failed.")
        return jsonify({
            "msg": "Something went wrong. Please try again.",
            "error": str(e)
        }), 500

@auth_bp.post("/send-otp")
@jwt_required()
def send_otp():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    receiver_email, name = user.email, user.full_name
    create_otp = generate_otp()

    success = EmailOTPService.send_otp_email(receiver_email, name, create_otp)
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
