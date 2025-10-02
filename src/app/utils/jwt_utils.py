"""
JWT Utils module
"""

from datetime import datetime, timedelta

from jose import jwt, JWTError

from ..config import settings

SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30


def create_access_token(sub: str, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = {
        "sub": str(sub),
        "exp": datetime.utcnow() + timedelta(minutes=expires_delta)
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(sub: str, expires_delta: int = REFRESH_TOKEN_EXPIRE_DAYS):
    """Create a refresh token with longer duration"""
    to_encode = {
        "sub": str(sub),
        "exp": datetime.utcnow() + timedelta(days=expires_delta),
        "type": "refresh"
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_token_pair(sub: str):
    """Create both access_token and refresh_token"""
    access_token = create_access_token(sub)
    refresh_token = create_refresh_token(sub)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


def verify_token(token: str, token_type: str = "access") -> str | None:
    """Verifies a token and returns the user_id if valid"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None

        if token_type == "refresh":
            if payload.get("type") != "refresh":
                return None

        return user_id
    except JWTError:
        return None


def verify_refresh_token(token: str) -> str | None:
    """Specifically verifies a refresh token"""
    return verify_token(token, token_type="refresh")
