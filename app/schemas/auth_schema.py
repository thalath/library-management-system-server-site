from marshmallow import fields, validate, validates, ValidationError, Schema

class LoginSchema(Schema):
    email = fields.Email(
        required=True
    )
    
    password = fields.String(
        required = True,
        load_only=True
    )
    
class ChangePasswordSchema(Schema):
    current_passowrd = fields.String(
        required=True,
        load_only=True
    )
    
    new_password = fields.String(
        required=True,
        load_only=True,
        validate=validate.Length(min=8)
    )
    
class ForgetPasswordSchema(Schema):
    email = fields.Email(
        required=True
    )
    
class ResetPasswordSchema(Schema):
    token = fields.String(
        required=True
    )
    
    new_password = fields.String(
        required=True,
        load_only=True,
        validate=validate.Length(min=8)
    )