from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.services.user_service import UserService
from app.models.user import User
from app.models.role import Role
from middleware.permission_extended import permission_required
from extensions import db
import re


user_bp = Blueprint("users", __name__, url_prefix="/users")

@user_bp.get("/")
@jwt_required()
@permission_required("user.view")
def index():
    users = UserService.get_all()
    if users is None:
        return jsonify({
            "msg": "Users not found.",
            "status": 404
        }), 404

    if users is not None:
        return jsonify({
            "msg": "Users retrived successfully",
            "status": 200,
            "data": [user.to_dict() for user in users]
        }), 200

    return jsonify({
        "msg": "An internal backend error occured.",
        "status": 500
    }), 500


@user_bp.get("/detail/<int:user_id>")
@jwt_required()
@permission_required("user.detail")
def detail(user_id: int):
    user = UserService.get_by_id(user_id)
    if user is None:
        return jsonify({
            "msg": f"User with ID: {user_id} was not found",
            "status": 404
        }), 404

    if user is not None:
        return jsonify({
            "msg": "User retrived successfully",
            "status": 200,
            "data": user.to_dict()
        }), 200

    return jsonify({
        "msg": "An internal Backend error occured.",
        "status": 500
    }), 500

@user_bp.post("/create")
@jwt_required()
@permission_required("user.create")
def create():
    data = request.get_json()
    if not data:
        return jsonify({
            "msg": "Body request is required.",
            "status": 400
        }), 400

    if data and data is not None:
        role_id = data.get("role_id") or None
        username = data.get("username", "").lower().strip()
        email = data.get("email", "").strip()
        password = data.get("password","")
        confirmation_password = data.get("confirmation_password", "")
        full_name = data.get("full_name", "").strip()

        errors: list[str] = []

        if not username:
            errors.append("Username is rquired.")
            
        if not full_name:
            errors.append("Full Name is required")

        if not email:
            errors.append("Email is require.")

        email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
        if email and not re.match(email_pattern, email):
            errors.append("Invalid email format.")

        if not password:
            errors.append("Strong password is required.")

        if password:
            if len(password) < 8:
                errors.append("Password must be contained at least 8 characters.")

            if not re.search(r"[a-z]", password):
                errors.append("Pasword must contained at least one lowercase character.")

            if not re.search(r"[A-Z]", password):
                errors.append("Password must contained at least one uppercase character.")

            if not re.search(r"[0-9]", password):
                errors.append("Password must contained at least one digit.")

            if not re.search(r"[!@#$%^&*()_+{}:';<>?.,/-=|]", password):
                errors.append("Password must contained at one special character.")

            if password != confirmation_password:
                errors.append("Password must matched")

        existing_role_ids = db.session.scalars(db.select(Role.id).order_by(Role.id)).all()

        if role_id:
            if not any(ex_ids == role_id for ex_ids in existing_role_ids):
                errors.append("Role that's chosen was not exist.")

        exists_username = User.query.filter_by(username=username).first()

        if exists_username:
            errors.append("Username is already taken.")

        exists_email = User.query.filter_by(email=email).first()

        if exists_email:
            errors.append("Email is already registered.")

        if errors:
            return jsonify({
                "msg": "Invalid or Missing Data fields",
                "error": [error for error in errors],
                "status": 400
            }), 400

        safe_user_data = {
                "username": username,
                "full_name": full_name,
                "email": email,
                "is_active": data.get("is_active", True)
        }
        try:
            user = UserService.create(safe_user_data, password, role_id)

            return jsonify({
                "msg": "User created successfully",
                "data": user.to_dict(),
                "status": 201
            }), 201
        except Exception as e:
            print("BACKEND ERROR OCCURED: ", e)
            raise e

    return jsonify({
        "msg": "An internal backend error occured.",
        "status": 500
    }), 500

@user_bp.put("/edit/<int:user_id>")
@jwt_required()
@permission_required("user.edit")
def edit(user_id: int):
    user = UserService.get_by_id(user_id)
    if not user or user is None:
        return jsonify({
            "msg": f"User with ID: {user_id} was not found",
            "status": 404
        }), 404

    data = request.get_json()
    if not data or data is None:
        return jsonify({
            "msg": "Body request is required.",
            "status": 400,
        }), 400

    if data or data is not None:
        username = data.get("username", user.username)
        full_name = data.get("full_name", user.full_name)
        email = data.get("email", user.email).strip()
        password = data.get("password", "").strip()
        confirmation_password = data.get("confirmation_password", "").strip()
        
        default_ids = [e.id for e in user.roles]
        role_id = data.get("role_id", default_ids[0] if default_ids else None)
        errors: list[str] = []

        if not username:
            errors.append("Username is required.")

        if not full_name:
            errors.append("Full name is required.")
        
        if not email:
            errors.append("Emali is required.")

        email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
        if email and not re.match(email_pattern, email):
            errors.append("Invalid email format.")

        if not password:
             errors.append("strong password is required.")

        if password:
            if len(password) < 8:
                errors.append("Password must be contained at leat 8 characters.")

            if not re.search(r"[a-z]", password):
                errors.append("Password must contained at least one lowercase character.")
            
            if not re.search(r"[A-Z]", password):
                errors.append("Password must contained at least one uppercase character.")

            if not re.search(r"[0-9]", password):
                errors.append("Password must contained at least one digit.")

            if not re.search(r"[!@#$%^&*()_+~]", password):
                errors.append("Password must contained at least uppsercase character.")

            if password != confirmation_password:
                errors.append("Confirm must matched.")

        e_ids = db.session.scalars(db.select(Role.id).order_by(Role.id)).all()

        if not any(e_id == role_id for e_id in e_ids if role_id == e_id): # check if role_id is not exist and not same as it default 
            errors.append("Role id was not exists in role list")
        
        if not errors:
            exists_username = User.query.filter_by(username=username).first()
        
            if exists_username and exists_username.username is not user.username:
                errors.append("Username is already taken.")

            exists_email = User.query.filter_by(email=email).first()

            if exists_email and exists_email.email is not user.email:
                errors.append("Email is already registered.")

        if errors:
            return jsonify({
                "msg": "Invalid Data Fields.",
                "errors": [error for error in errors],
                "status": 400
            }), 400

        try:
            safe_new_user_data = {
                    "username": username,
                    "full_name": full_name,
                    "email": email,
                    "is_active": data.get("is_active", True)
            }

            new_user = UserService.update(user, safe_new_user_data, password, role_id)

            return jsonify({
                "msg": "User updated succesfully.",
                "status": 200,
                "data": new_user.to_dict()
            }), 200
        except Exception as e:
            print("BACKEND ERROR OCCURED: ", e)
            raise e
    return jsonify({
        "msg": "An internal backend error occured.",
        "status": 500
    }), 500


@user_bp.delete("/delete/<int:user_id>")
@jwt_required()
@permission_required("user.delete")
def delete(user_id: int):
    user = UserService.get_by_id(user_id)
    if not user or user is None:
        return jsonify({
            "msg": f"User with ID: {user_id} was not found.",
            "status": 404
        }), 404

    UserService.delete(user)

    return jsonify({
        "msg": "User deleted successfully",
        "status": 200
    }), 200
