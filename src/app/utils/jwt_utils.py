from datetime import datetime, timedelta
from jose import jwt, JWTError

SECRET_KEY = "CHANGE_ME"  # usar .env / Vault
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
    """Crea un refresh token con mayor duración"""
    to_encode = {
        "sub": str(sub),
        "exp": datetime.utcnow() + timedelta(days=expires_delta),
        "type": "refresh"  # Identificador del tipo de token
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_token_pair(sub: str):
    """Crea tanto access_token como refresh_token"""
    access_token = create_access_token(sub)
    refresh_token = create_refresh_token(sub)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # En segundos
    }


def verify_token(token: str, token_type: str = "access") -> str | None:
    """Verifica un token y retorna el user_id si es válido"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None

        # Verificar tipo de token si es refresh
        if token_type == "refresh":
            if payload.get("type") != "refresh":
                return None

        return user_id
    except JWTError:
        return None


def verify_refresh_token(token: str) -> str | None:
    """Verifica específicamente un refresh token"""
    return verify_token(token, token_type="refresh")
