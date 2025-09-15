# src/app/controllers/profile.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.schemas.user import UserProfileUpdate, UserProfileResponse, PasswordChangeRequest
from src.app.models.user import User
from src.app.db.session import get_async_session
from src.app.dependencies.auth import get_current_admin_user
from src.app.services.profile_service import profile_service

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Obtiene el perfil del usuario administrador actual"""
    try:
        user_profile = await profile_service.get_user_profile(
            user_id=current_user.id,
            session=session
        )
        return UserProfileResponse(
            id=user_profile.id,
            name=user_profile.name,
            email=user_profile.email,
            role=user_profile.role,
            is_active=user_profile.is_active
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener el perfil: {str(e)}"
        ) from e


@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Actualiza el perfil del usuario administrador actual"""
    try:
        # Validar que al menos un campo se esté actualizando
        if not any([profile_data.name, profile_data.email]):
            raise HTTPException(
                status_code=400,
                detail="Debe proporcionar al menos un campo para actualizar"
            )

        updated_user = await profile_service.update_user_profile(
            user_id=current_user.id,
            update_data=profile_data,
            session=session
        )

        return UserProfileResponse(
            id=updated_user.id,
            name=updated_user.name,
            email=updated_user.email,
            role=updated_user.role,
            is_active=updated_user.is_active
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar el perfil: {str(e)}"
        ) from e


@router.get("/settings", response_model=dict)
async def get_profile_settings(
    current_user: User = Depends(get_current_admin_user)
):
    """Obtiene configuraciones adicionales del perfil"""
    return {
        "user_id": current_user.id,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": (
            current_user.created_at.isoformat()
            if current_user.created_at else None
        ),
        "updated_at": (
            current_user.updated_at.isoformat()
            if current_user.updated_at else None
        ),
        "settings": {
            "can_update_profile": True,
            "can_change_password": True,
            "account_type": "Administrator"
        }
    }


@router.put("/me/password", response_model=dict)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Cambia la contraseña del usuario administrador actual"""
    try:
        success = await profile_service.change_password(
            user_id=current_user.id,
            password_data=password_data,
            session=session
        )

        if success:
            return {"message": "Contraseña actualizada exitosamente"}
        else:
            raise HTTPException(
                status_code=500,
                detail="Error al actualizar la contraseña"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al cambiar la contraseña: {str(e)}"
        ) from e
