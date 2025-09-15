# src/app/utils/security.py
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "CHANGE_ME"  # usar .env / Vault
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)

def verify_password(plain, hashed) -> bool:
    return pwd_ctx.verify(plain, hashed)

def create_access_token(sub: str, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = {"sub": str(sub), "exp": datetime.utcnow() + timedelta(minutes=expires_delta)}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None
