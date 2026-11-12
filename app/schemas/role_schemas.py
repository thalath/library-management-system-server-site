from marshmallow import Schema, validate, fields, validates, ValidationError, pre_load
from ..repositories.permission_repository import filter_permissions_by_id
from ..models.role import Role
from sqlalchemy import func

class RoleCreateSchema(Schema):
    
    name = fields.String(
        required=True,
        validate=validate.Length(min=3, max=50)
    )

    description = fields.String(
        validate=validate.Length(min=3, max=100)
    )
    
    permission_ids = fields.List(
        fields.Integer(),
        required=True,
        validate=validate.Length(min=1)
    )
    
    @pre_load
    def normalize_data(self, data, **kwargs):
        if not isinstance(data, dict):
            return
        
        data = data.copy()
        
        if isinstance(data.get("name"), str):
            data["name"] = data["name"].strip()
        
        return data

    @validates("name")
    def validate_name(self, value, **kwargs):
        
        if value is None:
            return
        
        existing_name = Role.query.filter(func.lower(Role.name)==value.lower()).first()

        if existing_name:
            raise ValidationError("The name already exists.")


class RoleUpdateSchema(Schema):
    
    def __init__(self, role_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role_id = role_id
    
    name = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(min=3, max=50),
    )
    
    description = fields.String(
        validate=validate.Length(max=100),
        required=False,
        allow_none=True
    )

    permission_ids = fields.List(
        fields.Integer(),
        required=False,
        allow_none=True,
    )
    
    @pre_load
    def normalize_data(self, data, **kwargs):
        if not isinstance(data, dict):
            return
        data = data.copy()

        if isinstance(data.get("name"), str):
            data['name'] = data['name'].strip()
        
        return data
    
    @validates("permission_ids")
    def validate_permissions(self, value, **kwargs):
        
        if value is None:
            return
        
        if len(value) != len(set(value)):
            raise ValidationError("Dumplicate permission IDs was not allowed.")
        
        permissions = filter_permissions_by_id(value)

        if len(permissions) != len(value):
            raise ValidationError("Some permissions do not exist.")
        
    
    @validates("name")
    def validate_name(self, value, **kwargs):
        
        if value is None:
            return
        
        value = value.strip()
        
        exist_name = Role.query.filter(
            func.lower(Role.name) == value.lower(),
            Role.id != self.role_id
        ).first()

        if exist_name:
            raise ValidationError("The name already exists.")


class RoleResponseSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(dump_only=True)
    description = fields.String(dump_only=True)
    
    permissions = fields.Method("get_permissions", dump_only=True)
    users = fields.Method("get_users", dump_only=True)

    def get_permissions(self, obj):
        return [perm.name for perm in obj.permissions]
    
    def get_users(self, obj):
        return [{"full_name": user.full_name, "email": user.email} for user in obj.users]