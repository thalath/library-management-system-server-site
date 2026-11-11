from extensions import db
from app.models.permission import Permission

def get_permission_by_id(perm_id: int):
    return Permission.query.get(perm_id)

def get_all_permissions():
    return Permission.query.all()

def filter_permissions_by_id(permission_ids):
    return Permission.query.filter(
        Permission.id.in_(permission_ids)
    ).all()

def add_permission(perm: Permission):
    db.session.add(perm)
    db.session.commit()

    return perm