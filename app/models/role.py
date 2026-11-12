from datetime import datetime
from extensions import db
from app.models.associations import role_permissions, user_roles
from typing import Dict, Any


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(100))

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    users = db.relationship("User", secondary=user_roles, back_populates="roles")
    permissions = db.relationship("Permission", secondary=role_permissions, back_populates="roles")

    def has_permission(self, permission_code: str) -> bool:
        return any(p.code == permission_code for p in self.permissions)

    def __repr__(self) -> str:
        return f"{self.id}"
