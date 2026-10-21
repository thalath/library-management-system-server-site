from extensions import db
from app.models.permission import Permission
from typing import List, Optional

class PermissionService:

    @staticmethod
    def get_all() -> List[Permission]:
        return Permission.query.order_by(Permission.code.desc()).all()

    @staticmethod
    def get_by_id(perm_id: int) -> Optional[Permission]:
        return db.session.get(Permission, perm_id)

    @staticmethod
    def create(data: dict) -> Permission:
        perm = Permission(
                code=data["code"],
                name=data["name"],
                module=data.get("module", "General"),
                description=data.get("description")
            )

        db.session.add(perm)
        db.session.commit()
        return perm

    @staticmethod
    def update(perm: Permission, data: dict) -> Permission:
        fields = ['name', 'code', 'module', 'description']
        for field in fields:
            if field in data:
                setattr(perm, field, data[field])

        db.session.commit()
        return perm

    @staticmethod
    def delete(perm: Permission) -> None:
        db.session.delete(perm)
        db.session.commit()


