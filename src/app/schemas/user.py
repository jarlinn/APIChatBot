"""
Schemas for Users
"""

from uuid import UUID
from typing import Optional
import re

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    """Schema for creating a user"""
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v):
        """Custom validator for emails with more friendly messages"""
        if not v:
            raise ValueError("Email is required")

        email_str = str(v)

        if "@" not in email_str:
            raise ValueError("Email must contain the '@' symbol")

        local_part, domain = email_str.rsplit("@", 1)

        if not local_part:
            raise ValueError("Email must have a part before the '@' symbol")

        if not domain:
            raise ValueError("Email must have a domain after the '@' symbol")

        if "." not in domain:
            raise ValueError(
                "Domain must contain at least one dot (e.g: gmail.com)"
            )

        invalid_domains = [".local", ".localhost", ".test", ".invalid"]
        if any(domain.endswith(invalid_domain) for invalid_domain in invalid_domains):
            raise ValueError(
                f"The domain '{domain}' is not valid. "
                "Use a real domain like gmail.com, outlook.com, etc."
            )

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email_str):
            raise ValueError(
                "The email format is not valid. "
                "It must be something like: usuario@dominio.com"
            )

        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """Validator for passwords"""
        if not v:
            raise ValueError("Password is required")

        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")

        return v


class UserRead(BaseModel):
    """Schema for user read"""
    id: UUID
    name: Optional[str] = None
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for token"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Time in seconds until expiration
    refresh_token: Optional[str] = None  # Token to renew the access_token


class PasswordResetRequest(BaseModel):
    """Schema for resetting a password request"""
    email: EmailStr


class PasswordReset(BaseModel):
    """Schema for resetting a password"""
    token: str
    new_password: str


class RefreshTokenRequest(BaseModel):
    """Schema for refreshing a token"""
    refresh_token: str


class UserProfileUpdate(BaseModel):
    """Schema for updating a user profile"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None

    class Config:
        json_schema_extra = {
            "example": {"name": "Juan Pérez", "email": "admin@ejemplo.com"}
        }


class UserProfileResponse(BaseModel):
    """Schema for user profile response"""
    id: str
    name: Optional[str] = None
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class PasswordChangeRequest(BaseModel):
    """Schema for changing a password"""
    current_password: str
    new_password: str

    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "current_password",
                "new_password": "new_password",
            }
        }


class EmailChangeRequest(BaseModel):
    """Schema for requesting email change"""
    new_email: EmailStr

    class Config:
        json_schema_extra = {
            "example": {"new_email": "nuevo@email.com"}
        }


class EmailChangeConfirm(BaseModel):
    """Schema for confirming email change"""
    token: str
    new_email: EmailStr

    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123def456",
                "new_email": "nuevo@email.com"
            }
        }
