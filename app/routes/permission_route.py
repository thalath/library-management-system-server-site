from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from extensions import db
from middleware.permission_extended import permission_required
from app.services.permission_service import PermissionService
from app.schemas.permission_schema import PermissionResponseSchema, PermissionCreateSchema, PermissionUpdateSchema

perm_bp = Blueprint("permissions", __name__, url_prefix="/permissions")

@perm_bp.get("/")
@jwt_required()
@permission_required("permission.view")
def index():
    try:
        perms = PermissionService.get_all()
        response = PermissionResponseSchema(many=True)
        
        if not perms:
            return jsonify({
                "message": f"Permission not found.",
                "status": 404
            }), 404
            
        return jsonify(response.dump(perms)), 200
    
    except ValidationError as v_e:
        return jsonify({
            "message": "Invalid or missing fields.",
            "errors": v_e.messages,
            "status": 422
        }), 422
        
    except Exception as e:
        return jsonify({
            "message": "Exception Error, Please check error and try again.",
            "status": str(e)
        }), 500
        

@perm_bp.get("/detail/<int:perm_id>")
@jwt_required()
@permission_required("permission.detail")
def detail(perm_id: int):
    
    try:
        perm = PermissionService.get_by_id(perm_id)
        response = PermissionResponseSchema()
        if perm is None:
            return jsonify({
                "message": f"Permission with ID {perm_id} was not found.",
                "status": 404
            }), 404
        return jsonify(response.dump(perm)), 200
    
    except Exception as e:
        return jsonify({
            "message": "Exception errors, Please check errors and try again.",
            "errors": str(e),
            "status": 500
        }), 500

@perm_bp.post("/create")
@jwt_required()
@permission_required("permission.create")
def create():
    try:
        schema = PermissionCreateSchema()
        data = schema.load(
            request.get_json(silent=True) or {}
        )
        response = PermissionResponseSchema()
        
        perm = PermissionService.create(data)
        
        return jsonify(response.dump(perm)), 201
    
    except ValidationError as v_e:
        return jsonify({
            "message": "Invalid or missinf fields, Please try again.",
            "errors": v_e.messages,
            "status": 422
        }), 422
        
    except Exception as e:
        return jsonify({
            "message": "Exception errors, Please check error and try again.",
            "status": 500,
            "errors": str(e)
        }), 500


@perm_bp.put("/edit/<int:perm_id>")
@jwt_required()
@permission_required("permission.edit")
def edit(perm_id: int):
    schema = PermissionUpdateSchema(perm_id=perm_id)
    response = PermissionResponseSchema()
    
    try:
        perm = PermissionService.get_by_id(perm_id)
        data = schema.load(
            request.get_json(silent=True) or {}
        )

        if perm is None:
            return jsonify({
                "message": f"Permissio with ID {perm_id} was not found",
                "status": 404
            }), 404
            
        new_perm = PermissionService.update(perm, data)
        return jsonify(response.dump(new_perm)), 200
    
    except ValidationError as err:
        return jsonify({
            "message": "Invalid or missing fields.",
            "errors": err.messages,
            "status": 422
        }), 422
        
    except Exception as e:
        return jsonify({
            "message": "Exception Error, Please check error and try again,",
            "errors": str(e),
            "status": 500
        }), 500

@perm_bp.delete("/delete/<int:perm_id>")
@jwt_required()
@permission_required("permission.delete")
def delete(perm_id: int):
    perm = PermissionService.get_by_id(perm_id)
    if perm is None:
        return jsonify({
            "msg": f"Permission with ID: {perm_id} was not found",
            "status": 404
        }), 404

    PermissionService.delete(perm)
    return jsonify({
        "msg": "Permission deleted successfully.",
        "status": 200
    }), 200
