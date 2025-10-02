"""
Password hashing utilities
"""
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """return a hash password"""
    return pwd_ctx.hash(password)

def verify_password(plain, hashed) -> bool:
    """verify if the password is hashed"""
    return pwd_ctx.verify(plain, hashed)
