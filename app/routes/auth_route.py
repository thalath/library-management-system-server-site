from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request, current_app
from marshmallow import ValidationError
from flask_jwt_extended import (jwt_required, create_access_token, 
                                create_refresh_token, get_jwt_identity,
                                decode_token, get_jwt, set_access_cookies,
                                set_refresh_cookies, unset_jwt_cookies)

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
from app.schemas.user_schema import UserCreateSchema


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/email_verification")
@jwt_required()
def email_verification():
    
    data = request.get_json()
    claim = get_jwt()
    
    print("JWT CLAIMS:", claim)
    print("PURPOSE:", repr(claim.get("purpose")))

    try:
        if claim.get("purpose") != "email_verification":
            return jsonify({
                "message": "Invalid verification"
            }), 403
            
        otp = data.get("otp")
        user_id = int(get_jwt_identity())
        
        user = UserService.get_by_id(user_id)
        print(user.id)

        if not user:
            return jsonify({
                "message": "User not found",
                "status": 404
            }), 404
            
        if user.is_verified:
            return jsonify({
                "message": "Email already verified,",
                "status": 403
            }), 403
        
        otp_record = EmailOTP.query.filter_by(
            user_id=user_id,
            purpose="email_verification",
            is_used=False
        ).order_by(
            EmailOTP.created_at.desc()
        ).first()
        
        if not otp_record:
            return jsonify({
                "message": "Verification OTP not found.",
                "status": 404
            }), 404
            
        if datetime.utcnow() > otp_record.expired_at:
            return jsonify({
                "message": "OTP has expired."
            }), 400
            
        if not verify_otp_hash(otp, otp_record.otp_hash):
            otp_record.attempts += 1
            db.session.commit()
            return jsonify({
                "message": "OTP incorrect.",
                "remainning": max(0, 5 - otp_record.attempts)
            }), 400
            
        otp_record.is_used = True
        user.is_verified = True
        
        db.session.commit()
        
        access_token = create_access_token(identity=str(user_id))
        refresh_token = create_refresh_token(identity=str(user_id))
        
        response = jsonify({"Email verified successfully."})
        
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)       

        return response, 200
    
    except ValidationError as err:
        return jsonify({
            "message": "Ivalid or missing fileds.",
            "errors": err.messages
        }), 422
            
    except Exception as e:
        db.session.rollback()

        return jsonify({
            "msg": "email verification failed. Please try again later.",
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
    
    except Exception as e:
        return jsonify({
            "message": "Exception error",
            "errors": str(e)
        }), 500


@auth_bp.post("/register")
def register():

    try:
        schema = UserCreateSchema()
        
        data = schema.load(
            request.get_json(silent=True) or {}
        )
        
        password = data.pop("password", None)
        data.pop("confirmation_password", None)
        data.pop("role_id", None)
        
        email = data.get("email")
        full_name = data.get("full_name")

        default_role = Role.query.filter_by(name="User").first()
        default_role_id = default_role.id if default_role else None
        
        user = UserService.create(data, password, default_role_id)
        
        otp = generate_otp()
        EmailOTPService.send_otp_email(email, full_name, otp)

        data = {
            "purpose": "email_verification",
            "expired_at": datetime.utcnow() + timedelta(minutes=5)
        }

        EmailOTPService.create_email_otp(data, user.id, otp)
        
        verification_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "purpose": "email_verification"
            },
            expires_delta=timedelta(minutes=100)
        )
        
        response = jsonify({
            "message": "Registered successfully, Please ",
            "status": 201
        })
        
        set_access_cookies(response, verification_token)
        return response, 201
    
    except ValidationError as err:
        return jsonify({
            "message": "Invalid or missing fields.",
            "errors": err.messages
        }), 422

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
