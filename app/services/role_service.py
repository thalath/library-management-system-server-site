from extensions import db
from app.models.role import Role
from app.models.permission import Permission

from typing import List, Optional

class RoleService:
    @staticmethod
    def get_all() -> List[Role]:
        return Role.query.order_by(Role.name.asc()).all()

    @staticmethod
    def get_by_id(role_id: int) -> Optional[Role]:
        return db.session.get(Role, role_id)

    @staticmethod
    def create(data: dict, permission_ids: Optional[List[int]] = None) -> Role:
        role = Role(
                name=data["name"],
                description=data["description"]

            )
        if permission_ids is not None:
            permission = db.session.scalars(
                    db.select(Permission).filter(
                        Permission.id.in_(permission_ids)
                    )
            ).all()

            role.permissions = list(permission)

        db.session.add(role)
        db.session.commit()
        return role

    @staticmethod
    def update(role: Role, data: dict, permission_ids: Optional[List[int]] = None) -> Role:
        role.name =data['name']
        role.description=data['description']
        
        if permission_ids is not None:
            perms: List[Permission] = []
            perms = db.session.scalars(
                    db.select(Permission).filter(
                        Permission.id.in_(permission_ids)
                    )
                ).all()
            role.permissions = list(perms)

        db.session.commit()
        return role

    @staticmethod
    def delete(role: Role) -> None:
        db.session.delete(role)
        db.session.commit()

