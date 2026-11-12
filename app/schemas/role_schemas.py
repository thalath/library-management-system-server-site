from marshmallow import Schema, validate, fields, validates, ValidationError
from ..repositories.role_repository import get_role_by_name
from ..repositories.permission_repository import filter_permissions_by_id

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


    @validates("name")
    def validate_name(self, value, **kwargs):
        
        existing_name = get_role_by_name(value)

        if existing_name:
            raise ValidationError("The name already exists.")


class RoleUpdateSchema(Schema):
    
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
        
        exist_name = get_role_by_name(value)

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
        return [{"full_name": user.full_name, "email": user.email } for user in obj.users]