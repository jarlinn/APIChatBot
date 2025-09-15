# src/app/schemas/user.py
from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: UUID
    name: Optional[str] = None
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Tiempo en segundos hasta la expiración
    refresh_token: Optional[str] = None  # Token para renovar el access_token


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Juan Pérez",
                "email": "admin@ejemplo.com"
            }
        }


class UserProfileResponse(BaseModel):
    id: str
    name: Optional[str] = None
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "contraseña_actual",
                "new_password": "nueva_contraseña_segura"
            }
        }
