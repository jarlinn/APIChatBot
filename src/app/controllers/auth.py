# src/app/controllers/auth.py
from datetime import datetime, timedelta
import secrets
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from src.app.schemas.user import (
    UserCreate, Token, PasswordResetRequest, PasswordReset, RefreshTokenRequest
)
from src.app.models.user import User
from src.app.db.session import get_async_session
from sqlalchemy.future import select
from src.app.utils.hashing import hash_password, verify_password
from src.app.utils.jwt_utils import create_token_pair, verify_refresh_token
from src.app.services.email_service import email_service
from src.app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=None)
async def register(
    payload: UserCreate,
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    session=Depends(get_async_session)
):
    q = await session.execute(select(User).filter_by(email=payload.email))
    if q.scalars().first():
        raise HTTPException(status_code=400, detail="Email exists")

    if not x_admin_token or x_admin_token != settings.admin_view:
        raise HTTPException(status_code=403, detail="Invalid admin token")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password)
    )
    session.add(user)
    await session.commit()
    return {"msg": "created"}


@router.post("/token", response_model=Token)
async def login(form: UserCreate, session=Depends(get_async_session)):
    q = await session.execute(select(User).filter_by(email=form.email))
    user = q.scalars().first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Crear par de tokens (access + refresh)
    token_data = create_token_pair(sub=user.id)
    return {
        "access_token": token_data["access_token"],
        "token_type": "bearer",
        "expires_in": token_data["expires_in"],
        "refresh_token": token_data["refresh_token"]
    }


@router.post("/password-reset-request")
async def request_password_reset(
    payload: PasswordResetRequest, session=Depends(get_async_session)
):
    """Solicitar un reset de contraseña"""
    q = await session.execute(select(User).filter_by(email=payload.email))
    user = q.scalars().first()
    if not user:
        # Por seguridad, no revelamos si el email existe o no
        return {
            "msg": "Si el email existe, recibirás instrucciones para resetear tu contraseña"
        }
    
    # Generar token y establecer expiración (24 horas)
    reset_token = secrets.token_urlsafe(32)
    expiration = datetime.utcnow() + timedelta(hours=24)
    
    # Guardar token en la base de datos
    user.reset_token = reset_token
    user.reset_token_expires = expiration
    await session.commit()
    
    # Enviar email con el token de recuperación
    email_sent = await email_service.send_password_reset_email(
        to_email=user.email,
        reset_token=reset_token,
        user_name=user.email.split("@")[0]  # Usar parte del email como nombre
    )
    
    if email_sent:
        return {
            "msg": "Si el email existe, recibirás instrucciones para resetear tu contraseña"
        }
    else:
        # Si falla el envío del email, limpiar el token de la BD
        user.reset_token = None
        user.reset_token_expires = None
        await session.commit()
        
        return {
            "msg": "Error al enviar el correo. Inténtalo de nuevo más tarde.",
            "error": True
        }


@router.post("/password-reset")
async def reset_password(
    payload: PasswordReset, session=Depends(get_async_session)
):
    """Resetear la contraseña usando el token"""
    q = await session.execute(
        select(User).filter_by(reset_token=payload.token)
    )
    user = q.scalars().first()
    
    if (
        not user or not user.reset_token_expires or 
        user.reset_token_expires < datetime.utcnow()
    ):
        raise HTTPException(
            status_code=400, detail="Token inválido o expirado"
        )
    
    # Actualizar contraseña
    user.hashed_password = hash_password(payload.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    await session.commit()
    
    return {"msg": "Contraseña actualizada exitosamente"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    payload: RefreshTokenRequest, session=Depends(get_async_session)
):
    """Renovar access token usando refresh token"""
    user_id = verify_refresh_token(payload.refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=401, detail="Refresh token inválido o expirado"
        )
    
    # Verificar que el usuario aún existe y está activo
    q = await session.execute(select(User).filter_by(id=user_id))
    user = q.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=401, detail="Usuario no encontrado o inactivo"
        )
    
    # Crear nuevo par de tokens
    token_data = create_token_pair(sub=user.id)
    return {
        "access_token": token_data["access_token"],
        "token_type": "bearer",
        "expires_in": token_data["expires_in"],
        "refresh_token": token_data["refresh_token"]
    }
