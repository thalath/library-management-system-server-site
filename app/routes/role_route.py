from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from extensions import db
from middleware.permission_extended import permission_required
from app.schemas.role_schemas import RoleResponseSchema, RoleCreateSchema, RoleUpdateSchema
from app.services.role_service import RoleService
from app.repositories.permission_repository import filter_permissions_by_id
from app.repositories.role_repository import get_role_by_id

role_bp = Blueprint("roles", __name__, url_prefix="/roles")


@role_bp.get("/")
@jwt_required()
@permission_required("role.view")
def index():
    try:
        roles = RoleService.get_all()
        response = RoleResponseSchema(many=True)

        if not roles:
            return jsonify({
                "message": "Roles not found.",
                "status": 404
            }), 404
            
        return jsonify({
            "message": "Role retrived, successfully.",
            "Role": response.dump(roles),
        }), 200
    
    except ValidationError as v_e:
        return jsonify({
            "mssage": "Invalid or missing fields",
            "errors": v_e.messages
        }), 422
        
    except Exception as e:
        return jsonify({
            "message": "retrives errors, Please try again later.",
            "errors": e
        }), 500

@role_bp.get("detail/<int:role_id>")
@jwt_required()
@permission_required("role.detail")
def detail(role_id: int):
    try:
        role_response_schema = RoleResponseSchema()
        role = RoleService.get_by_id(role_id)

        if not role:
            return jsonify({
                "message": f"Role with ID {role_id} was not found",
                "status": 404
            }), 404
        return jsonify(role_response_schema.dump(role)), 200
    
    except ValidationError as v_e:
        return jsonify({
            "message": "Invalid or missing fields",
            "errors": v_e.messages
        }), 422
    except Exception as e:
        return jsonify({
            "message": "retrived error, Please check the errors and try again.",
            "errors": e
        }), 500

@role_bp.post("/create")
@jwt_required()
@permission_required("role.create")
def create():
    try:
        schema = RoleCreateSchema()
        response_schema = RoleResponseSchema()
        data = schema.load(
            request.get_json(silent=True) or {}
        )
        
        permission_ids = data.pop("permission_ids")
        if permission_ids:
            permissions = filter_permissions_by_id(permission_ids)
            if len(permissions) != len(set(permission_ids)):
                return jsonify({
                    "message": "Some permissions do not exist."
                }), 422
    
        role = RoleService.create(data, permission_ids)
        
        return jsonify(response_schema.dump(role)), 201
    
    except ValidationError as v_e:
        return jsonify({
            "message": "Invalide or missing fields.",
            "errors": v_e.messages
        }), 422
        
    except Exception as e:
        return jsonify({
            "message": "Role errors, Please check the errors and try again.",
            "errors": e
        })
    

@role_bp.put("/edit/<int:role_id>")
@jwt_required()
@permission_required("role.edit")
def edit(role_id: int):
    try:
        
        role = get_role_by_id(role_id)
        response = RoleResponseSchema()
        
        schema = RoleUpdateSchema()
        data = schema.load(
            request.get_json(silent=True) or {}
        )
        
        permission_ids = data.pop("permission_ids", None)
        
        updated_role = RoleService.update(role, data, permission_ids)
        
        return jsonify({
            "message": "Role updated successfully.",
            "Role": response.dump(updated_role)
        }), 200
        
    except ValidationError as v_e:
        return jsonify({
            "message": "Invalid or missing fileds, Please check error and try again later.",
            "error": v_e.messages
        }), 422


@role_bp.delete("/delete/<int:role_id>")
@jwt_required()
@permission_required("role.delete")
def delete(role_id: int):
    try:
        role = get_role_by_id(role_id)
        if not role:
            return jsonify({
                "message": f"Role with ID: {role_id} was not exist.",
                "status": 404
            }), 404
            
        RoleService.delete(role)
        return jsonify({
            "message": "Role deleted successfully.",
            "success": True
        }), 200
        
    except Exception:
        return jsonify({
            "message": "Exception Error, Please check & try again later.",
            "success": False
        }), 500

