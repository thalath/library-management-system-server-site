from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models.user import User


def permission_required(permission_code: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user:
                return jsonify({
                    "msg": "User not found",
                    "status": 404
                }), 404

            if user and not user.is_active:
                return jsonify({
                    "msg": "You account is inactive",
                    "status": 403
                }),403

            if user and not user.has_permission(permission_code):
                return jsonify({
                    "msg": "You do not have permission to perform this action.",
                    "status": 403
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator
