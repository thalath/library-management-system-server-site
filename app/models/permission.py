from datetime import datetime
from extensions import db
from app.models.associations import role_permissions
from typing import Dict, Any

class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(60), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    module = db.Column(db.String(70), nullable=False, default="General")
    description = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    roles = db.relationship("Role", secondary=role_permissions, back_populates="permissions")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "module": self.module,
            "description": self.description
        }

    def __repr__(self) -> str:
        return f"<Permissions {self.code}>"
