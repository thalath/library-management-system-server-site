from extensions import db
from app.models.user import User
from app.models.role import Role
from typing import List, Optional

class UserService:
    @staticmethod
    def get_all() -> List[User]:
        return User.query.order_by(User.id.desc()).all()

    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        return db.session.get(User, user_id)


    @staticmethod
    def create(data: dict, password: str, role_id: Optional[int] = None) -> User:
        user = User(**data)
        user.set_password(password)
        
        if role_id:
            role = db.session.get(Role, role_id)
            
            if role is None:
                raise ValueError("Selected role does not exist.")
            
            user.roles.append(role)
            
        db.session.add(user)
        db.session.commit()
        return user
            

    @staticmethod
    def update(user: User, data: dict, password: Optional[str] = None, role_id: Optional[int] = None) -> User:
        fields = ["username", "full_name", "is_active", "email"]

        for field in fields:
            if field in data:
                setattr(user, field, data[field])

        if password:
            user.set_password(password)

        if role_id:
            role = db.session.get(Role, role_id)
            if role is None:
                raise ValueError("Selected roles does not exists.")
            
            user.roles.append(role)

        db.session.commit()
        return user

    @staticmethod
    def delete(user:User) -> None:
        db.session.delete(user)
        db.session.commit()
