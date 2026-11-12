from app.models.role import Role
from app.models.permission import Permission
from app.repositories.permission_repository import filter_permissions_by_id
from app.repositories.role_repository import add_role, get_all_roles, get_role_by_id

from typing import List, Optional
from extensions import db

class RoleService:
    @staticmethod
    def get_all() -> List[Role]:
        return get_all_roles()

    @staticmethod
    def get_by_id(role_id: int) -> Optional[Role]:
        return get_role_by_id(role_id)

    @staticmethod
    def create(data: dict, permission_ids: Optional[List[int]] = None,) -> Role:
        role = Role(**data)
        
        if permission_ids:
            permissions = filter_permissions_by_id(permission_ids)
            
            role.permissions = permissions
        add_role(role)
        return role

    @staticmethod
    def update(role: Role, data: dict, permission_ids: Optional[List[int]] = None) -> Role:
        
        if "name" in data:
            role.name=data['name']
        if "description" in data:
            role.description=data['description']
        
        if permission_ids:
            permissions = filter_permissions_by_id(permission_ids or [])
            
            role.permissions = permissions

        db.session.commit()
        return role

    @staticmethod
    def delete(role: Role) -> None:
        db.session.delete(role)
        db.session.commit()

