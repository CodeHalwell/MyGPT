"""
Marshmallow schemas for input validation across all API endpoints and forms.
Provides comprehensive data validation, serialization, and security.
"""

from marshmallow import Schema, fields, validate, validates, ValidationError
from models import User, Tag
import re


class UserRegistrationSchema(Schema):
    """Schema for user registration form validation."""
    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=64, error="Username must be between 3 and 64 characters"),
            validate.Regexp(
                r'^[a-zA-Z0-9_-]+$',
                error="Username can only contain letters, numbers, underscores, and hyphens"
            )
        ]
    )
    email = fields.Email(
        required=True,
        validate=validate.Length(max=120, error="Email must be less than 120 characters")
    )
    password = fields.Str(
        required=True,
        validate=[
            validate.Length(min=8, max=128, error="Password must be between 8 and 128 characters"),
            validate.Regexp(
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
                error="Password must contain at least one lowercase letter, one uppercase letter, and one digit"
            )
        ]
    )

    @validates('username')
    def validate_username_unique(self, value, **kwargs):
        if User.query.filter_by(username=value).first():
            raise ValidationError('Username already exists')

    @validates('email')
    def validate_email_unique(self, value, **kwargs):
        if User.query.filter_by(email=value).first():
            raise ValidationError('Email already registered')


class UserLoginSchema(Schema):
    """Schema for user login form validation."""
    username = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=64, error="Username is required")
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=128, error="Password is required")
    )


class ForgotPasswordSchema(Schema):
    """Schema for forgot password form validation."""
    email = fields.Email(
        required=True,
        validate=validate.Length(max=120, error="Email must be less than 120 characters")
    )


class ResetPasswordSchema(Schema):
    """Schema for password reset form validation."""
    password = fields.Str(
        required=True,
        validate=[
            validate.Length(min=8, max=128, error="Password must be between 8 and 128 characters"),
            validate.Regexp(
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
                error="Password must contain at least one lowercase letter, one uppercase letter, and one digit"
            )
        ]
    )


class ChatMessageSchema(Schema):
    """Schema for chat message validation."""
    message = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=10000, error="Message must be between 1 and 10,000 characters"),
            validate.Regexp(
                r'^[\s\S]*\S[\s\S]*$',
                error="Message cannot be empty or contain only whitespace"
            )
        ]
    )


class StreamChatSchema(Schema):
    """Schema for streaming chat parameters."""
    model = fields.Str(
        required=False,
        validate=validate.OneOf(
            ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo', 'claude-3-opus', 'claude-3-sonnet', 
             'claude-3-haiku', 'gemini-pro', 'mistral-large', 'mistral-medium'],
            error="Invalid AI model selected"
        ),
        load_default='gpt-4o'
    )


class UpdateUsernameSchema(Schema):
    """Schema for username update validation."""
    new_username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=64, error="Username must be between 3 and 64 characters"),
            validate.Regexp(
                r'^[a-zA-Z0-9_-]+$',
                error="Username can only contain letters, numbers, underscores, and hyphens"
            )
        ]
    )
    current_password = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=128, error="Current password is required")
    )

    @validates('new_username')
    def validate_username_unique(self, value, **kwargs):
        if User.query.filter_by(username=value).first():
            raise ValidationError('Username already exists')


class UpdatePasswordSchema(Schema):
    """Schema for password update validation."""
    current_password = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=128, error="Current password is required")
    )
    new_password = fields.Str(
        required=True,
        validate=[
            validate.Length(min=8, max=128, error="Password must be between 8 and 128 characters"),
            validate.Regexp(
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
                error="Password must contain at least one lowercase letter, one uppercase letter, and one digit"
            )
        ]
    )
    confirm_password = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=128, error="Password confirmation is required")
    )

    @validates('new_password')
    def validate_passwords_match(self, value, **kwargs):
        confirm_password = self.context.get('confirm_password')
        if confirm_password and value != confirm_password:
            raise ValidationError('New passwords do not match')


class AdminToggleSchema(Schema):
    """Schema for admin toggle operations."""
    is_admin = fields.Bool(required=True)


class CreateTagSchema(Schema):
    """Schema for tag creation validation."""
    name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=50, error="Tag name must be between 1 and 50 characters"),
            validate.Regexp(
                r'^[a-zA-Z0-9\s\-_]+$',
                error="Tag name can only contain letters, numbers, spaces, underscores, and hyphens"
            )
        ]
    )
    color = fields.Str(
        required=False,
        validate=validate.Regexp(
            r'^#[0-9A-Fa-f]{6}$',
            error="Color must be a valid hex color code (e.g., #FF0000)"
        ),
        load_default=None
    )

    @validates('name')
    def validate_tag_name_unique(self, value, **kwargs):
        if Tag.query.filter_by(name=value.strip().lower()).first():
            raise ValidationError('Tag already exists')


class UpdateTagSchema(Schema):
    """Schema for tag update validation."""
    color = fields.Str(
        required=True,
        validate=validate.Regexp(
            r'^#[0-9A-Fa-f]{6}$',
            error="Color must be a valid hex color code (e.g., #FF0000)"
        )
    )


# Validation utility functions
def validate_json_data(schema_class, data):
    """
    Utility function to validate JSON data against a schema.
    Returns (validated_data, errors) tuple.
    """
    schema = schema_class()
    try:
        validated_data = schema.load(data)
        return validated_data, None
    except ValidationError as err:
        # Return empty dict instead of None to prevent KeyError issues
        return {}, err.messages


def validate_form_data(schema_class, form_data, context=None):
    """
    Utility function to validate form data against a schema.
    Returns (validated_data, errors) tuple.
    """
    if context:
        schema = schema_class()
        schema.context = context
    else:
        schema = schema_class()
    try:
        validated_data = schema.load(form_data)
        return validated_data, None
    except ValidationError as err:
        # Return empty dict instead of None to prevent KeyError issues
        return {}, err.messages


def get_validation_errors_string(errors):
    """
    Convert validation errors dict to a user-friendly string.
    """
    if not errors:
        return ""
    
    error_messages = []
    for field, messages in errors.items():
        if isinstance(messages, list):
            error_messages.extend(messages)
        else:
            error_messages.append(str(messages))
    
    return "; ".join(error_messages)