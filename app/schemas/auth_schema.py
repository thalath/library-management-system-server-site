from marshmallow import fields, validate, validates_schema, ValidationError, Schema
import re

# ========= Strong password helper ================
def strong_password(value):
    password = value or ""
    
    if len(password) < 8:
        raise ValidationError("Password must contain at least 8 characters.")
    
    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase character.")

    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase character.")
    
    if not re.search(r"[0-9]", password):
        raise ValidationError("Password must contain at least one digit.")

    if not re.search(r"[^A-Za-z0-9\s]", password):
        raise ValidationError("Password must contain at least one special character.")
    
class LoginSchema(Schema):
    email = fields.Email(
        required=True,
        error_messages = {
            "required": "Email is required."
        }
    )
    
    password = fields.String(
        required = True,
        load_only=True,
        validate=validate.Length(min=8),
        error_messages={
            "required": "Password is required."
        }
    )
    
class UpdatePasswordSchema(Schema):
    current_passowrd = fields.String(
        required=True,
        load_only=True
    )
    
    new_password = fields.String(
        required=True,
        load_only=True,
        validate=[strong_password]
    )
    
    confirmation_password = fields.String(
        required=True,
        load_only=True,
        validate=[strong_password]
    )
    
    
    @validates_schema
    def validate_confirmation_password(self, data, **kwargs):
        if data['new_password'] != data['current_password']:
            raise ValidationError({
                "confirmation_password": [
                    "Passwor must be matched."
                ]
            })
    
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
        validate=[strong_password]
    )
    
    @validates_schema
    def validate_confirmation_password(self, data, **kwargs):
        if data['password'] != data['confirmation_password']:
            raise ValidationError({
                "confirmation_password": [
                    "Password must matched."
                ]
            })