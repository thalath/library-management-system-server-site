from flask import Blueprint, jsonify, request
from app.services.role_service import RoleService
from flask_jwt_extended import jwt_required

from middleware.permission_extended import permission_required

from app.models.role import Role
from app.models.permission import Permission
from extensions import db

role_bp = Blueprint("roles", __name__, url_prefix="/roles")

@role_bp.get("/")
@jwt_required()
@permission_required("role.view")
def index():
    roles = RoleService.get_all()
    if not roles or roles is None:
        return jsonify({
            "msg": "Roles not found.",
            "status": 404
        }), 404

    if roles or roles is not None:
        return jsonify({
            "msg": "Roles retrivced successfully.",
            "status": 200,
            "data": [role.to_dict() for role in roles]
        }), 200

    return jsonify({
        "msg": "Internal Backend Error occured",
        "status": 500
        }), 500

@role_bp.get("detail/<int:role_id>")
@jwt_required()
@permission_required("role.detail")
def detail(role_id: int):
    role = RoleService.get_by_id(role_id)
    if not role or role is None:
        return jsonify({
            "msg": f"Role with ID: {role_id} was not found.",
            "status": 404
        }), 404

    if role or role is not None:
        return jsonify({
            "msg": "Role retrived successfully.",
            "status": 200,
            "data": role.to_dict()
        }), 200
    return jsonify({
        "msg": "Internal Backend error occured.",
        "status": 500
    }), 500

@role_bp.post("/create")
@jwt_required()
@permission_required("role.create")
def create():
    data = request.get_json()
    if not data or data is None:
        return jsonify({
            "msg": "Body request is required.",
            "status": 400
        }), 400

    if data or data is not None:
        name = data.get("name", "").strip()
        description = data.get("description") or "_"
        permission_ids = data.get("permission_ids") or []

        errors: dict[str, list[str]] = {}
        if not name:
            errors.setdefault("name", []).append("Role name is required.")
        elif len(name) > 50:
            errors.setdefault("name", []).append("Role name cannot execced 50 characters.")

        if len(description) > 249:
            errors.setdefault("description", []).append("Role description cannot execced 250 characters.")

        existed_perm = Permission.query.filter_by(code="user.view").first()
        default_perm_ids = permission_ids if permission_ids else [existed_perm.id]

        if permission_ids:
            existed_ids = set(db.session.scalars(db.select(Permission.id)))
            invalid_ids = set(permission_ids) - existed_ids
            if invalid_ids:
                errors.setdefault("permission_ids", []).append(
                        f"The flollowing permission IDs do not exist: {sorted(list(invalid_ids))}")
            elif permission_ids and not isinstance(permission_ids, list):
                errors.setdefault("Permission ids", []).append("Permission must be a list.")
        
        if not errors:
            existed_name = Role.query.filter_by(name=name).first()
            if existed_name:
                errors.setdefault("role_id", []).append("Role name is already taken.")
            
 
        if errors:
            return jsonify({
                "msg": "Invalid Role Field.",
                "error": errors,
                "status": 400
            }), 400

        try:
            
            safe_role_data = {
                    "name": name,
                    "description": description
            }


            role = RoleService.create(safe_role_data, default_perm_ids)

            return jsonify({
                "msg": "Role created successfully.",
                "status": 201,
                "data": role.to_dict()
            }), 201
        except Exception as e:
            print("BACKEND ERROR OCCURED", e)
            raise e

    return jsonify({
        "msg": "An internal backend error occured.",
        "status": 500
    }), 500

@role_bp.put("/edit/<int:role_id>")
@jwt_required()
@permission_required("role.edit")
def edit(role_id: int):
    role = RoleService.get_by_id(role_id)
    if not role or role is None:
        return jsonify({
            "msg": f"Role with ID: {role_id} was not found",
            "status": 404
        }), 404
    data = request.get_json()
    if not data or data is None:
        return jsonify({
            "msg": "Body request is required.",
            "status": 400
        }), 400

    if data or data is not None:
        name = data.get("name", role.name)
        description = data.get("description", role.description)
        permission_ids = data.get("permission_ids", [perm.id for perm in role.permissions])        
        errors: list[str] = []
        if not name:
            errors.append("Role name is required.")

        if permission_ids:
            if not isinstance(permission_ids, list):
                errors.append("Permission ids, must be list values.")
            
            exist_perm_ids = set(db.session.scalars(db.select(Permission.id)))
            if not all(ep in exist_perm_ids for ep in permission_ids): # check if permission is not in permissions table
                errors.append("Permission is not exist.")
                

        if not errors:
            exists_roles = db.session.scalars(db.select(Role).order_by(Role.name)).all()
            if any(name.lower() == r.name.lower() for r in exists_roles if r.id != role.id): # check if role name is exist and not same as default
                errors.append("Role name is already taken.")

        if errors:
            return jsonify({
                "msg": "Invalid or Missing Field.",
                "status": 400,
                "error": [error for error in errors],
            }), 400

        
        safe_role_data = {
            "name": name,
            "description": description
        }

        try:
            new_role = RoleService.update(role, safe_role_data, permission_ids)
            return jsonify({
                "msg": "Role updated successfully.",
                "status": 200,
                "data": new_role.to_dict()
            }), 200
        except Exception as e:
            print("BACKEND ERROR ERROR.", e)

    return jsonify({
        "msg": "An internal backend error occured.",
        "status": 500
    }), 500

@role_bp.delete("/delete/<int:role_id>")
@jwt_required()
@permission_required("role.delete")
def delete(role_id: int):
    role = RoleService.get_by_id(role_id)
    if not role or role is None:
        return jsonify({
            "msg": f"Role with ID: {role_id} was not found.",
            "status": 404
        }), 404

    if role and role is not None:
        RoleService.delete(role)
        return jsonify({
            "msg": "Role deleted successfully.",
            "status": 200
        }), 200

    return jsonify({
        "msg": "An internal backend error occured.",
        "status": 500
    }), 500


