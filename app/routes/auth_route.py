from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import (jwt_required, create_access_token, 
                                create_refresh_token, get_jwt_identity,
                                decode_token, get_jwt, set_access_cookies,
                                set_refresh_cookies, unset_jwt_cookies)

from app.services.user_service import UserService
from app.models.user import User
from app.models.token_blocklist import TokenBlocklist
from app.models.role import Role
from extensions import db
import re

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

        access_token = create_access_token(identity=str(new_user.id))
        refresh_token = create_refresh_token(identity=str(new_user.id))

        response = jsonify({"msg": "Login successfully"})
            
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        return response, 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "msg": f"An internal backend error occured: {str(e)}",
            "status": 500
        }), 500

@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=str(current_user_id))
    response = jsonify({"msg": "Refresh successfully"})
    
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
