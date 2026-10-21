from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import re
from wtforms.validators import ValidationError
from app.models.associations import user_roles
from typing import Dict, Any

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), unique=True, nullable=False)
    full_name = db.Column(db.String(80), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    roles = db.relationship("Role", secondary=user_roles, back_populates="users")

    def set_password(self, password: str) -> None:
        if len(password) < 8:
            raise ValidationError("Passowr must be contained at least 8 characters.")
        if not re.search(r"[a-z]", password):
            raise ValidationError("Password must be contained at least one lowercase character.")
        if not re.search(r"[A-Z]", password):
            raise ValidationError("Password must be contained at least one uppercase character.")
        if not re.search(r"[!@#$%^&*()_+-=,./;'\{}]", password):
            raise ValidationError("Password must be contained at least one special character.")
        if not re.search(r"[0-9]", password):
            raise ValidationError("Password must be contained at least one digit")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name: str) -> bool:
        return any(
                role.name == role_name
                for role in self.roles
        )

    def get_permission_codes(self) -> set[str]:
        return {
            perm.code
            for role in self.roles
            for perm in role.permissions
        }
    
    def has_permission(self, permission_code: str) -> bool:
        return permission_code in self.get_permission_codes()


    def has_role(self, role_name: str) ->bool:
        return any(
                role.name == role_name
                for role in self.roles
        )
    def get_permission_codes(self) -> set[str]:
        return {
                perm.code
                for role in self.roles
                for perm in role.permissions
        }

    def has_permissiosn_codes(self, permission_codes: str) -> bool:
        return permission_code in self.get_permission_codes()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "is_active": self.is_active,
            "full_name": self.full_name,
            "email": self.email,
            "role": [role.to_dict() for role in self.roles],
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def __repr__(self) -> str:
        return f"<Users {self.username}>"
