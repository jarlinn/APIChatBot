import uuid
from sqlalchemy import Column, String, Text, TIMESTAMP, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db.database import Base
from ..schemas.question import QuestionStatus


class Question(Base):
    __tablename__ = "questions"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_text = Column(Text, nullable=False)
    context_text = Column(Text, nullable=True)
    context_type = Column(String(20), nullable=False, default="text")
    context_file = Column(String(500), nullable=True)  # Ruta del archivo
    category_id = Column(String(36), ForeignKey("categories.id"), 
                         nullable=False)
    # tags = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, 
                    default=QuestionStatus.PENDING.value)
    model_response = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    # Relaciones
    category = relationship("Category", back_populates="questions")


class ChunkEmbedding(Base):
    __tablename__ = "chunk_embeddings"
    id = Column(String(36), primary_key=True, 
                default=lambda: str(uuid.uuid4()))
    question_id = Column(String(36), nullable=False)
    embedding = Column(Text, nullable=True)  # Para SQLite
    payload = Column(Text, nullable=True)
    similarity = Column(String(50), nullable=True)