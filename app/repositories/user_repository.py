from extensions import db
from app.models.user import User

class UserRepository:
    def __init__(self):
        self.db = db

    def get_all():
        return User.query.order_by(User.id.desc()).all()

    def get_by_email(email: str):
        return User.query.filter_by(email=email).first()

    def create(self, user: User) -> User:
        self.db.session.add(user)
        self.db.session.commit()

        return user
