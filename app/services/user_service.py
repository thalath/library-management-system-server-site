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
            
            user.roles.append(role)
            
        add_user(user)
        return user
            

    @staticmethod
    def update(user: User, data: dict, password: Optional[str] = None, role_id: Optional[int] = None) -> User:
                
        if "username" in data:
            user.username = data["username"]
        
        if "full_name" in data:
            user.full_name = data["full_name"]
            
        
        if "is_active" in data:
            user.is_active = data.get("is_active")
            
        if "is_verified" in data:
            user.is_verified = data.get("is_verified")

        if "password" in data:
            user.set_password(password)

        if "role_id" in data:
            role_id = data["role_id"]
            
            if role_id is None:
                user.roles = []
            
            else:
                role = get_role_by_id(role_id)
                user.roles = [role]

        db.session.commit()
        return user

    @staticmethod
    def delete(user: User) -> None:
        db.session.delete(user)
        db.session.commit()
