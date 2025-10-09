# src/app/controllers/auth.py
from datetime import datetime, timedelta, timezone
import secrets
import string
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from src.app.schemas.user import (
    UserCreate, Token, PasswordResetRequest, PasswordReset, RefreshTokenRequest,
    EmailChangeRequest, EmailChangeConfirm
)
from src.app.models.user import User
from src.app.db.session import get_async_session
from src.app.dependencies.auth import get_current_active_user
from sqlalchemy.future import select
from src.app.utils.hashing import hash_password, verify_password
from src.app.utils.jwt_utils import create_token_pair, verify_refresh_token
from src.app.services.email_service import email_service
from src.app.config import settings

logger = logging.getLogger(__name__)

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
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Generar token y establecer expiración (24 horas)
    reset_token = secrets.token_urlsafe(32)
    expiration = datetime.now(timezone.utc) + timedelta(hours=24)
    
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
        user.reset_token_expires < datetime.now(timezone.utc)
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


@router.post("/email-change-request")
async def request_email_change(
    payload: EmailChangeRequest,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session)
):
    """Solicitar cambio de email - envía código de verificación al email actual"""
    try:
        # Verificar que el nuevo email no esté en uso
        existing_user = await session.execute(
            select(User).filter_by(email=payload.new_email)
        )
        if existing_user.scalars().first():
            raise HTTPException(status_code=400, detail="Email already in use")

        # Verificar que no sea el mismo email actual
        if current_user.email == payload.new_email:
            raise HTTPException(status_code=400, detail="New email must be different from current email")

        # Generar código de verificación
        verification_code = secrets.token_hex(6).upper()  # Código de 12 caracteres alfanumérico
        expiration = datetime.now(timezone.utc) + timedelta(hours=24)

        # Guardar código y email pendiente en la base de datos
        current_user.email_change_token = verification_code
        current_user.email_change_token_expires = expiration
        current_user.pending_email = payload.new_email
        await session.commit()

        # Enviar email con código de verificación al email ACTUAL
        email_sent = await email_service.send_email_change_verification(
            to_email=current_user.email,  # Email actual del usuario
            verification_code=verification_code,
            new_email=payload.new_email
        )

        if email_sent:
            return {
                "msg": "Verification code sent to your current email address",
                "expires_in": "24 hours"
            }
        else:
            # Si falla el envío, limpiar los campos
            current_user.email_change_token = None
            current_user.email_change_token_expires = None
            current_user.pending_email = None
            await session.commit()

            raise HTTPException(
                status_code=500,
                detail="Failed to send verification email. Please try again."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in request_email_change: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/email-change-confirm")
async def confirm_email_change(
    payload: EmailChangeConfirm,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session)
):
    """Confirmar código inicial y enviar confirmación al nuevo email"""
    try:
        # Verificar que el usuario tenga un token pendiente
        if not current_user.email_change_token:
            raise HTTPException(status_code=400, detail="No email change request found")

        # Verificar que el token no haya expirado
        if (
            not current_user.email_change_token_expires or
            current_user.email_change_token_expires < datetime.now(timezone.utc)
        ):
            raise HTTPException(status_code=400, detail="Verification code expired")

        # Verificar que el código coincida
        if current_user.email_change_token != payload.token.upper():
            raise HTTPException(status_code=400, detail="Invalid verification code")

        # Verificar que el email pendiente coincida
        if current_user.pending_email != payload.new_email:
            raise HTTPException(status_code=400, detail="Email mismatch")

        # Verificar una vez más que el nuevo email no esté en uso
        existing_user = await session.execute(
            select(User).filter_by(email=payload.new_email)
        )
        if existing_user.scalars().first():
            raise HTTPException(status_code=400, detail="Email already in use")

        # Generar token único para confirmar desde el nuevo email
        confirm_token = secrets.token_urlsafe(32)

        # Actualizar usuario: mantener email actual, agregar token de confirmación
        current_user.email_change_confirm_token = confirm_token
        # No limpiamos los otros campos aún - se limpian al completar
        await session.commit()

        # Enviar email de confirmación al NUEVO email
        email_sent = await email_service.send_email_change_confirmation(
            to_email=payload.new_email,  # Nuevo email
            confirm_token=confirm_token,
            old_email=current_user.email  # Email actual para contexto
        )

        if email_sent:
            return {
                "msg": "Verification successful. Check your new email to complete the change.",
                "next_step": "Check your new email and click the confirmation link"
            }
        else:
            # Si falla el envío, revertir cambios
            current_user.email_change_confirm_token = None
            await session.commit()

            raise HTTPException(
                status_code=500,
                detail="Failed to send confirmation email. Please try again."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in confirm_email_change: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/email-change-complete")
async def complete_email_change(
    token: str,
    session=Depends(get_async_session)
):
    """Completar cambio de email desde el link enviado al nuevo email"""
    try:
        # Buscar usuario por token de confirmación
        q = await session.execute(
            select(User).filter_by(email_change_confirm_token=token)
        )
        user = q.scalars().first()

        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired confirmation link")

        # Verificar que tenga email pendiente
        if not user.pending_email:
            raise HTTPException(status_code=400, detail="No pending email change found")

        # Verificar que el token inicial no haya expirado
        if (
            not user.email_change_token_expires or
            user.email_change_token_expires < datetime.now(timezone.utc)
        ):
            raise HTTPException(status_code=400, detail="Confirmation link expired")

        # Guardar email anterior para notificación
        old_email = user.email

        # Generar contraseña temporal segura
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(12))

        # Completar el cambio de email y establecer contraseña temporal
        user.email = user.pending_email
        user.hashed_password = hash_password(temp_password)  # Cambiar a contraseña temporal
        user.email_change_token = None
        user.email_change_token_expires = None
        user.pending_email = None
        user.email_change_confirm_token = None
        await session.commit()

        # Enviar notificación con contraseña temporal al NUEVO email
        try:
            await email_service.send_email_change_success_notification(
                to_email=user.email,  # Nuevo email
                temporary_password=temp_password,
                old_email=old_email
            )
        except Exception as e:
            logger.error(f"Could not send success notification to new email {user.email}: {e}")
            # No fallar la operación completa si el email falla

        # Opcional: Enviar notificación al email anterior
        try:
            await email_service.send_email(
                to_email=old_email,
                subject="📧 Tu email fue actualizado - ChatBot UFPS",
                html_content=f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #2c3e50;">📧 Email Actualizado</h2>
                    <p>Tu dirección de correo electrónico ha sido cambiada exitosamente.</p>
                    <p><strong>Nuevo email:</strong> {user.email}</p>
                    <p>Si no realizaste este cambio, contacta inmediatamente a soporte.</p>
                </div>
                """,
                text_content=f"Tu email fue actualizado a: {user.email}"
            )
        except Exception as e:
            logger.warning(f"Could not send notification to old email {old_email}: {e}")

        return {
            "msg": "Email updated successfully! Check your new email for login instructions.",
            "new_email": user.email,
            "temporary_password_sent": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in complete_email_change: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
