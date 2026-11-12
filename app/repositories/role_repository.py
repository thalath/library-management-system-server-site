from extensions import db
from app.models.role import Role

def get_role_by_id(role_id: int):
    return Role.query.get(role_id)


def get_role_by_name(name):
    return Role.query.filter_by(name=name).first()

def get_all_roles():
    return Role.query.all()

def add_role(role: Role):
    db.session.add(role)
    db.session.commit()
    
    return role
