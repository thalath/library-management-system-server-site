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
from app.models.role import Role
from app.models.token_blocklist import TokenBlocklist
from app.schemas.auth_schema import LoginSchema, ForgetPasswordSchema, ResetPasswordSchema
from app.repositories.user_repository import filter_user_by_email, get_user_by_id
from app.utils.otp import generate_otp
from app.schemas.user_schema import UserCreateSchema


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/verify")
@jwt_required()
def email_verification():
    
    data = request.get_json()
    claim = get_jwt()

    try:
        
        otp = data.get("otp")
        user_id = int(get_jwt_identity())
        
        user = UserService.get_by_id(user_id)

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
        
        verify = EmailOTPService.verify(user.id, otp, claim.get("purpose"))
        
        if verify:
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            response = jsonify({"message": "Email verified successfully."})
            
            user.is_verified = True
            set_access_cookies(response, access_token)
            set_refresh_cookies(response, refresh_token)       
            db.session.commit()
            return response, 200
        
        return jsonify({
            "message": "Invalid or expired verification code.",
        }), 400
            
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

        if not user:
            return jsonify({
                "message": "user not found."
            }), 404
        
        otp = generate_otp()
        EmailOTPService.send_otp(email, full_name, otp)
        EmailOTPService.create_otp(
            user_id=user.id,
            otp=otp,
            minutes=5
        )
        
        verification_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "purpose": "email_verification"
            },
            expires_delta=timedelta(minutes=5)
        )
        
        response = jsonify({
            "message": "Registered successfully, Please try again",
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
            "message": "Registration Failed, Please try again.",
            "error": str(e)
        }), 500


@auth_bp.post("/forgot-password")
def forgot_password():

    otp = generate_otp()

    try:
        schema = ForgetPasswordSchema()
        data = schema.load(request.get_json(silent=True) or {})
        
        user = filter_user_by_email(data["email"])
        
        if not user:
            return jsonify({
                "message": "Selected email does not exist.",
                "status": 404
            }), 404
            
        token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "purpose": "forget_password"
            },
            expires_delta=timedelta(minutes=5)
        )
        
        reset_url = (
            f"{current_app.config["FRONTEND_URL"]}"
            f"/reset-password?token={token}"
        )

        email_otp = EmailOTPService.create_otp(
            purpose="forget_password",
            minutes=5,
            user_id=user.id,
            otp=otp
        )
        if email_otp:
            EmailOTPService.send_otp(user.email, user.full_name, otp)
        
        response = jsonify({
            "message": "OTP was sent, Please verify your OTP.",
            "info": "Temperary access token was created,",
            "reset_url": reset_url
        })
        
        return response, 200
    
    except ValidationError as err:
        return jsonify({
            "message": "Invalid or missing fields.",
            "errors": err.messages
        }), 422
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Cannot send OTP to Email")

        return jsonify({
            "message": "Internal Error accured.",
            "errors": str(e)
        }), 500

@auth_bp.post("/reset-password")
@jwt_required(locations=["headers"])
def reset_password():
    schema = ResetPasswordSchema()
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    
    if claims.get("purpose") != "forget_password":
        return jsonify({
            "message": "Invalid passwor reset token"
        }), 403
    try:
            
        data = schema.load(
            request.get_json(silent=True) or {}
        )
        
        new_password = data.pop("new_password", None)
        data.pop("confirmation_password", None)
    
        user = get_user_by_id(user_id)
        UserService.update(user=user,password=new_password)
        return jsonify({
            "message": "password reset successfully."
        }), 200
        
    except ValidationError as err:
        return jsonify({
            "message": "Invalid or missing fields",
            "errors": err.messages
        }), 422

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
