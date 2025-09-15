import uuid
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func
from ..db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="admin")
    is_active = Column(Boolean, default=True)
    reset_token = Column(String(100), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
