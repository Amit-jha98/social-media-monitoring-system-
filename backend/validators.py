# backend/validators.py
"""Marshmallow schemas for request validation."""
import re
from marshmallow import Schema, fields, validate, validates, ValidationError


class KeywordSchema(Schema):
    """Validate keyword creation/update requests."""
    keyword = fields.String(
        required=True,
        validate=[
            validate.Length(min=1, max=255, error="Keyword must be 1-255 characters"),
        ]
    )

    @validates("keyword")
    def validate_keyword_content(self, value):
        """Ensure keyword doesn't contain dangerous characters."""
        value = value.strip()
        if not value:
            raise ValidationError("Keyword cannot be empty or whitespace only")
        if not re.match(r'^[\w\s\-#@.,]+$', value, re.UNICODE):
            raise ValidationError(
                "Keyword contains invalid characters. "
                "Only letters, numbers, spaces, #, @, -, . and , are allowed"
            )


class KeywordUpdateSchema(Schema):
    """Validate keyword update requests."""
    new_name = fields.String(
        required=True,
        validate=[
            validate.Length(min=1, max=255, error="Keyword must be 1-255 characters"),
        ]
    )

    @validates("new_name")
    def validate_keyword_content(self, value):
        value = value.strip()
        if not value:
            raise ValidationError("Keyword cannot be empty or whitespace only")
        if not re.match(r'^[\w\s\-#@.,]+$', value, re.UNICODE):
            raise ValidationError("Keyword contains invalid characters")


class HoneypotProfileSchema(Schema):
    """Validate honeypot profile creation."""
    platform = fields.String(
        required=True,
        validate=[
            validate.OneOf(
                ["Telegram", "WhatsApp", "Instagram"],
                error="Platform must be Telegram, WhatsApp, or Instagram"
            )
        ]
    )
    username = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100)
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=8, max=255, error="Password must be at least 8 characters")
    )
    email = fields.Email(required=True)


class UserRegistrationSchema(Schema):
    """Validate user registration."""
    username = fields.String(
        required=True,
        validate=[
            validate.Length(min=3, max=50, error="Username must be 3-50 characters"),
            validate.Regexp(r'^[\w]+$', error="Username can only contain letters, numbers, and underscores"),
        ]
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=8, max=128, error="Password must be 8-128 characters")
    )
    email = fields.Email(required=False, load_default=None)


class UserLoginSchema(Schema):
    """Validate user login."""
    username = fields.String(required=True, validate=validate.Length(min=1, max=50))
    password = fields.String(required=True, validate=validate.Length(min=1, max=128))


class PaginationSchema(Schema):
    """Validate pagination parameters."""
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=50, validate=validate.Range(min=1, max=200))


class ScrapingRequestSchema(Schema):
    """Validate scraping request."""
    batch_size = fields.Integer(load_default=100, validate=validate.Range(min=1, max=500))
