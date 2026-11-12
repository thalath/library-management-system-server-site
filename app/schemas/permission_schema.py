from marshmallow import validate, Schema, validates, fields, pre_load, ValidationError
from sqlalchemy import func

from app.repositories.permission_repository import filter_permissions_by_name
from app.models.permission import Permission

class PermissionCreateSchema(Schema):
    
    code = fields.String(
        required=True,
        validate=validate.Length(min=3, max=60)
    )
    
    name = fields.String(
        required=True,
        validate=validate.Length(min=3,max=120)
    )
    
    module = fields.String(
        load_default="General",
        validate=validate.Length(min=3, max=60)
    )
    
    description = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=120)
    )
    
    @pre_load
    def normalize_data(self, data, **kwargs):
        if not isinstance(data, dict):
            return
        
        data =data.copy()

        if isinstance(data.get("code"), str):
            data['code'] = data['code'].strip().lower()
            
        if isinstance(data.get("name"), str):
            data['name'] = data['name'].strip()
            
        if isinstance(data.get("module"), str):
            data['module'] = data['module'].strip()

        return data
    
    @validates("code")
    def validate_code(self, value, **kwargs):
        if value is None:
            return
        value = value.strip()
        
        exist_code = Permission.query.filter(
            func.lower(Permission.code) == value.lower()
        ).first()
        
        if exist_code:
            raise ValidationError("Code already exist.")
    
        
class PermissionUpdateSchema(Schema):
    def __init__(self, perm_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.perm_id = perm_id
        
    code = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(min=3, max=60),
    )
    
    name = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(min=3, max=120)
    )
    
    module = fields.String(
        load_default="General",
        validate=validate.Length(max=70)
    )
    
    description = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=1200)
    )
    
    @pre_load
    def normalize_data(self, data, **kwargs):
        if not isinstance(data, dict):
            return
        
        data = data.copy()

        if isinstance(data.get("code"), str):
            data["code"] = data["code"].strip().lower()
        
        if isinstance(data.get("name"), str):
            data["name"] = data["name"].strip()
            
        return data
    
    @validates("code")
    def validate_code(self, value, **kwargs):
        if value is None:
            return
        
        value = value.strip()

        exist_code = Permission.query.filter(
            func.lower(Permission.code) == value.lower(),
            Permission.id != self.perm_id
        ).first()
        
        if exist_code:
            raise ValidationError("Code already exist.")
        
        
class PermissionResponseSchema(Schema):
    
    id = fields.Integer(dump_only=True)
    code = fields.String(dump_only=True)
    name = fields.String(dump_only=True)
    module = fields.String(dump_only=True)
    description = fields.String(dump_only=True)

    roles = fields.Method("get_roles", dump_only=True)

    def get_roles(self, obj):
        return [role.name for role in obj.roles]