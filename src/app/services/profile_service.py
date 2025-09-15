# src/app/services/profile_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from src.app.models.user import User
from src.app.schemas.user import UserProfileUpdate, PasswordChangeRequest
from src.app.utils.hashing import hash_password, verify_password


class ProfileService:
    """Servicio para gestión de perfil de usuario"""

    async def get_user_profile(
        self, user_id: str, session: AsyncSession
    ) -> User:
        """Obtiene el perfil de un usuario por ID"""
        query = await session.execute(select(User).filter_by(id=user_id))
        user = query.scalars().first()

        if not user:
            raise HTTPException(
                status_code=404, detail="Usuario no encontrado"
            )

        return user

    async def update_user_profile(
        self,
        user_id: str,
        update_data: UserProfileUpdate,
        session: AsyncSession
    ) -> User:
        """Actualiza el perfil de un usuario"""
        # Obtener el usuario actual
        query = await session.execute(select(User).filter_by(id=user_id))
        user = query.scalars().first()

        if not user:
            raise HTTPException(
                status_code=404, detail="Usuario no encontrado"
            )

        # Verificar si el nuevo email ya está en uso por otro usuario
        if update_data.email and update_data.email != user.email:
            email_query = await session.execute(
                select(User).filter_by(email=update_data.email)
            )
            existing_user = email_query.scalars().first()
            if existing_user and existing_user.id != user_id:
                raise HTTPException(
                    status_code=400,
                    detail="El correo electrónico ya está en uso"
                )

        # Actualizar campos si se proporcionan
        update_dict = update_data.dict(exclude_unset=True)

        for field, value in update_dict.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)

        # Guardar cambios
        await session.commit()
        await session.refresh(user)

        return user

    async def change_password(
        self,
        user_id: str,
        password_data: PasswordChangeRequest,
        session: AsyncSession
    ) -> bool:
        """Cambia la contraseña de un usuario"""
        # Obtener el usuario actual
        query = await session.execute(select(User).filter_by(id=user_id))
        user = query.scalars().first()

        if not user:
            raise HTTPException(
                status_code=404, detail="Usuario no encontrado"
            )

        # Verificar contraseña actual
        if not verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=400, detail="La contraseña actual es incorrecta"
            )

        # Actualizar con la nueva contraseña
        user.hashed_password = hash_password(password_data.new_password)

        # Guardar cambios
        await session.commit()

        return True


# Instancia global del servicio
profile_service = ProfileService()
