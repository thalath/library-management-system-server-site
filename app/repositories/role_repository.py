from extensions import db
from app.models.role import Role

def get_role_by_id(role_id: int):
    return db.session.get(Role, role_id)

def get_all_roles():
    return Role.query.all()

def filter_role_by_name(name):
    return Role.query.filter_by(name=name).first()

def add_role(role: Role):
    db.session.add(role)
    db.session.commit()
    
    return role
