from app.models.user import User
from extensions import db

def get_user_by_id(user_id: int):
    return User.query.get(user_id)

def get_user_by_email(email):
    return User.query.filter_by(email=email).first()

def get_user_by_username(username):
    return User.query.filter_by(username=username).first()


def get_all_users():
    return User.query.all()

def add_user(user: User):
    db.session.add(user)
    db.session.commit()

    return user