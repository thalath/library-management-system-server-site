from extensions import db
from app.models.permission import Permission
from typing import List, Optional
from app.repositories.permission_repository import add_permission, get_all_permissions, get_permission_by_id

class PermissionService:

    @staticmethod
    def get_all() -> List[Permission]:
        return get_all_permissions()

    @staticmethod
    def get_by_id(perm_id: int) -> Optional[Permission]:
        return get_permission_by_id(perm_id)

    @staticmethod
    def create(data: dict) -> Permission:
        
        perm = Permission(**data)
        add_permission(perm)
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


