from marshmallow import Schema, fields, validate, ValidationError, validates, validates_schema, pre_load
from ..models.user import User

import re


class UserCreateSchema(Schema):
    username = fields.String(
        required=True,
        validate=validate.Length(min=3, max=60)
    )

    full_name = fields.String(
        required=True,
        validate=validate.Length(min=2, max=80)
    )

    email = fields.Email(
        required=True,
        validate=validate.Length(max=120)
    )

    password = fields.String(
        required=True,
        load_only=True,
        validate=validate.Length(min=8),
    )
    
    confirmation_password = fields.String(
        required=True,
        load_only=True
    )
    
    role_id = fields.Integer(
        load_default=None,
        allow_none=True
    )
    
    is_active = fields.Boolean(
        load_default=True
    )
    
    @pre_load
    def normalize_data(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        
        data = data.copy()
        
        if isinstance(data.get("username"), str):
            data['username'] = data["username"].strip().lower()
            
        if isinstance(data.get("email"), str):
            data["email"] = data["email"].strip().lower()

        if isinstance(data.get("full_name"), str):
            data["full_name"] = data['full_name'].strip().lower()

        return data
    
    @validates("password")
    def validate_password(self, value, **kwargs):
        if len(value) < 8:
            raise ValidationError("Passowrd mus contain at least 8 characters.")
        
        if not re.search(r"[a-z]", value):
            raise ValidationError("Password must contain at least one lowercause character.")
        
        if not re.search(r"[A-Z]", value):
            raise ValidationError("Password must contain at least one uppercase character.")
        
        if not re.search(r"[0-9]", value):
            raise ValidationError("Password must contain at least one digit.")
        
        if not re.search(r"[^A-Za-z0-9\s]", value):
            raise ValidationError("Password must contain at least one special character.")
    
    @validates_schema
    def validate_confirmation_password(self,  data, **kwargs):
        if data.get("password") != data.get("confirmation_password"):
            raise ValidationError({
                "confirmation_password": [
                    "Passwords must be matched."
                ]
            })
    
    @validates("username")
    def validate_username(self, value, **kwargs):
        
        existing_username = User.query.filter_by(username=value).first()
        
        if existing_username:
            raise ValidationError("Username is already taken.")
        
    @validates("email")
    def validate_email(self, value, **kwargs):
        if not re.search(r"[\w\.-]+@[\w\.-]+\.\w+]", value):
            raise ValidationError("Invalid email format.")
        
        existing_email = User.query.filter_by(email=value).first()
        if existing_email:
            raise ValidationError("Email is already registered.")
    
class UserUpdateSchema(Schema):
    
    def __init__(self, user_id=None, **kwargs):
        self.user_id = user_id
    
    username = fields.String(validate=validate.Length(min=3, max=60))
    
    full_name = fields.String(validate=validate.Length(min=2, max=80))
    
    email = fields.Email(validate=validate.Length(max=120))
    
    is_active = fields.Boolean(allow_none=True)
    
    @validates("username")
    def validate_username(self, value, **kwargs):
        existing_user = User.query.filter(
            User.username == value,
            User.id != self.user_id
        ).first()
        
        if existing_user:
            raise ValidationError("Username already exists.")
        
    @validates("email")
    def validate_email(self, value, **kwargs):
        if not re.search(r"[\w\.-]+@[\w\.-]+\.\w+]", value):
            raise ValidationError("Invalid Email format.")
        
        existing_user = User.query.filter(
            User.email == value,
            User.id != self.user_id
        ).first()

        if existing_user:
            raise ValidationError("Email already exists.")
        
class UserResponseSchema(Schema):
    
    id = fields.Integer(dump_only=True)
    username = fields.String(dump_only=True)
    full_name = fields.String(dump_only=True)
    email = fields.String(dump_only=True)

    is_active = fields.Boolean(dump_only=True)
    is_verified = fields.Boolean(dump_only=True)

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    
    def get_roles(self, obj):
        return [role.name for role in obj.roles]