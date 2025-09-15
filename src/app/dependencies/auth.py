from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.app.utils.jwt_utils import verify_token
from src.app.models.user import User
from src.app.db.session import get_async_session
from sqlalchemy.future import select

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session=Depends(get_async_session)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Verificar token
    user_id = verify_token(token)
    if user_id is None:
        raise credentials_exception

    # Buscar usuario en la base de datos
    q = await session.execute(select(User).filter_by(id=user_id))
    user = q.scalars().first()
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin role required."
        )
    return current_user
