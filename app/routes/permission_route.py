from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from middleware.permission_extended import permission_required
from app.services.permission_service import PermissionService
from app.models.permission import Permission
from extensions import db

perm_bp = Blueprint("permissions", __name__, url_prefix="/permissions")

@perm_bp.get("/")
@jwt_required()
@permission_required("permission.view")
def index():
    perms = PermissionService.get_all()
    if perms is None:
        return jsonify({
            "msg": "permission not found.",
            "status": 404
        }), 404

    if perms or perms is not None:
        return jsonify({
            "msg": "permissions retrived successfully.",
            "status": 200,
            "data": [perm.to_dict() for perm in perms]
        }), 200

    return jsonify({
        "msg": "an internal backend error occured",
        "status": 500
    }), 500

@perm_bp.get("/detail/<int:perm_id>")
@jwt_required()
@permission_required("permission.detail")
def detail(perm_id: int):
    perm = PermissionService.get_by_id(perm_id)
    if not perm or perm is None:
        return jsonify({
            "msg": f"permission with id: {perm_id} was not found.",
            "status": 404
        }), 404

    if perm or perm is not None:
        return jsonify({
            "msg": "permission retrived successfully.",
            "status": 200,
            "data": perm.to_dict()
        }), 200

    return jsonify({
        "msg": "an internal backend error occured.",
        "status": 500
    }), 500


@perm_bp.post("/create")
@jwt_required()
@permission_required("permission.create")
def create():
    data = request.get_json()
    if not data:
        return jsonify({
            "msg": "body request is required.",
            "status": 400
        }), 400

    if data or data is not None:
        name = data.get("name", "").strip()
        code = data.get("code", "").strip()
        module = data.get("module", "General").strip()
        description = data.get("description", "_").strip()

        errors: list[str] = []
        if not name:
            errors.append("permission name is required.")

        if not code:
            errors.append("permission code is required.")

        if code:
            
            exist_codes = db.session.scalars(db.select(Permission.code).order_by(Permission.code)).all()
            if any(c_code.lower() == code.lower() for c_code in exist_codes):
                errors.append("Permission code is already taken.")
        if errors:
            return jsonify({
                "status": 400,
                "msg": "invalid fields.",
                "errors": [error for error in errors]
            }), 400

        sate_perm_data = {
                "name": name,
                "code": code.lower(),
                "module": module,
                "description": description
        }
        try:
            new_perm = PermissionService.create(sate_perm_data)
            return jsonify({
                "msg": "Permission created successfully.",
                "status": 201,
                "data": new_perm.to_dict()
            }), 201
        except Exception as e:
            print("BACKEND ERROR OCCURED: ", e)
            raise e

    return jsonify({
        "msg": "An internal backend error occured.",
        "status": 500
    }), 500

@perm_bp.put("/edit/<int:perm_id>")
@jwt_required()
@permission_required("permission.edit")
def edit(perm_id: int):
    perm = PermissionService.get_by_id(perm_id)
    if not perm or perm is None:
        return jsonify({
            "msg": f"Permission with ID: {perm_id} was not found.",
            "status": 404
        }), 404

    data = request.get_json()
    if not data or data is None:
        return jsonify({
            "msg": "Body request is required.",
            "status": 400
        }), 400

    if data or data is not None:
        name = data.get("name", perm.name).strip()
        module = data.get("module", perm.module).strip()
        code = data.get("code", perm.code).strip()
        description = data.get("description", perm.description).strip()

        exist_codes = db.session.scalars(db.select(Permission).order_by(Permission.code)).all()
        if any(code.lower() == c_perm.code.lower() for c_perm in exist_codes if c_perm.id != perm.id): # bugged taken or not in same id
            return jsonify({
                "msg": "Permission code is alreay taken.",
                "status": 400
            }), 400

        safe_perm_data = {
                "name": name,
                "code": code.lower(),
                "module": module,
                "description": description
        }
    new_perm = PermissionService.update(perm, safe_perm_data)
    return jsonify({
        "msg": "Permission updated successfully.",
        "status": 200,
        "data": new_perm.to_dict()
    }), 200

@perm_bp.delete("/delete/<int:perm_id>")
@jwt_required()
@permission_required("permission.delete")
def delete(perm_id: int):
    perm = PermissionService.get_by_id(perm_id)
    if not perm or perm is None:
        return jsonify({
            "msg": f"Permission with ID: {perm_id} was not found",
            "status": 404
        }), 404

    PermissionService.delete(perm)
    return jsonify({
        "msg": "Permission deleted successfully.",
        "status": 200
    }), 200
