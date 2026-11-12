from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from app.services.user_service import UserService
from app.models.user import User
from app.models.role import Role
from middleware.permission_extended import permission_required
from extensions import db
import re
from ..schemas.user_schema import UserCreateSchema, UserUpdateSchema, UserResponseSchema


user_bp = Blueprint("users", __name__, url_prefix="/users")

@user_bp.get("/")
@jwt_required()
@permission_required("user.view")
def index():
    users = UserService.get_all()
    response_schema = UserResponseSchema(many=True)
    if users is None:
        return jsonify({
            "message": "Users not found.",
            "status": 404
        }), 404

    if users:
        return jsonify({
            "message": "Users retrived successfully",
            "status": 200,
            "data": response_schema.dump(users)
        }), 200

    return jsonify({
        "message": "An internal backend error occured.",
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
    user_create_schema = UserCreateSchema()
    try:
        data = user_create_schema.load(
            request.get_json(silent=True) or {}
        )
        
        password = data.pop("password")
        data.pop("confirmation_password")
        
        role_id = data.pop("role_id")
        
        user = UserService.create(data, password, role_id)
        
        
        return jsonify({
            "message": "User created successfully.",
            "data": user_create_schema.dump(user),
            "status": 201
        }), 201
        
    except ValidationError as err:
        return jsonify({
            "message": "Invalid or missing data fields.",
            "errors": err.messages,
            "status": 422
        }), 422
        

@user_bp.put("/edit/<int:user_id>")
@jwt_required()
@permission_required("user.edit")
def edit(user_id: int):
    try:
        user = UserService.get_by_id(user_id)
        
        user_update_schema = UserUpdateSchema()
        response = UserResponseSchema()
        
        data = user_update_schema.load(
            request.get_json(silent=True) or {}
        )
        
        password = data.pop("password", None)
        role_id = data.pop("role_id", None)
        data.pop("is_active", None)
        
        new_user = UserService.update(user, data, password, role_id)
        
        return jsonify({
            "message": "User updated successfully.",
            "data": response.dump(new_user),
            "status": 200
        }), 200
        
    except ValidationError as err:
        return jsonify({
            "message": "Invalid or missing fields",
            "errors": err.messages,
            "status": 422
        }), 422
        
    except Exception as e:
        return jsonify({
            "message": "Error",
            "errors": str(e)
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
