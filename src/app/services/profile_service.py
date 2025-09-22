"""
Service for user profile management
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from src.app.models.user import User
from src.app.schemas.user import UserProfileUpdate, PasswordChangeRequest
from src.app.utils.hashing import hash_password, verify_password


class ProfileService:
    """Service for user profile management"""

    async def get_user_profile(
        self, user_id: str, session: AsyncSession
    ) -> User:
        """Get user profile by ID"""
        query = await session.execute(select(User).filter_by(id=user_id))
        user = query.scalars().first()

        if not user:
            raise HTTPException(
                status_code=404, detail="User not found"
            )

        return user

    async def update_user_profile(
        self,
        user_id: str,
        update_data: UserProfileUpdate,
        session: AsyncSession
    ) -> User:
        """Update user profile"""
        # Obtener el usuario actual
        query = await session.execute(select(User).filter_by(id=user_id))
        user = query.scalars().first()

        if not user:
            raise HTTPException(
                status_code=404, detail="User not found"
            )

        if update_data.email and update_data.email != user.email:
            email_query = await session.execute(
                select(User).filter_by(email=update_data.email)
            )
            existing_user = email_query.scalars().first()
            if existing_user and existing_user.id != user_id:
                raise HTTPException(
                    status_code=400,
                    detail="Email already in use"
                )

        update_dict = update_data.dict(exclude_unset=True)

        for field, value in update_dict.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)

        await session.commit()
        await session.refresh(user)

        return user

    async def change_password(
        self,
        user_id: str,
        password_data: PasswordChangeRequest,
        session: AsyncSession
    ) -> bool:
        """Change user password"""
        query = await session.execute(select(User).filter_by(id=user_id))
        user = query.scalars().first()

        if not user:
            raise HTTPException(
                status_code=404, detail="User not found"
            )

        if not verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=400, detail="Current password is incorrect"
            )

        user.hashed_password = hash_password(password_data.new_password)

        await session.commit()

        return True


profile_service = ProfileService()
