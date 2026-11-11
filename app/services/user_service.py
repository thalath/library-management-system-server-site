from extensions import db
from app.models.user import User
from typing import List, Optional
from app.repositories.user_repository import get_all_users, get_user_by_id, add_user
from app.repositories.role_repository import get_role_by_id

class UserService:
    @staticmethod
    def get_all() -> List[User]:
        return get_all_users()

    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        return get_user_by_id(user_id)


    @staticmethod
    def create(data: dict, password: str, role_id: Optional[int] = None) -> User:
        user = User(**data)
        user.set_password(password)
        
        if role_id:
            role = get_role_by_id(role_id)
            
            if role is None:
                raise ValueError("Selected role does not exist.")
            
            user.roles.append(role)
            
        add_user(user)
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
            role = get_role_by_id(role_id)
            if role is None:
                raise ValueError("Selected roles does not exists.")
            
            user.roles.append(role)

        db.session.commit()
        return user

    @staticmethod
    def delete(user: User) -> None:
        db.session.delete(user)
        db.session.commit()
