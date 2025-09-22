"""
Model for Questions
"""

import logging
import uuid

from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..db.database import Base
from ..schemas.question import QuestionStatus


class Question(Base):
    """
    Model for Questions
    Updated to include relationship with vector embeddings
    """
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_text = Column(Text, nullable=False)
    context_text = Column(Text, nullable=True)
    context_type = Column(String(20), nullable=False, default="text")
    context_file = Column(String(500), nullable=True)  # File path
    # Flexible hierarchy - at least modality is required
    modality_id = Column(String(36), ForeignKey("modalities.id"), nullable=False)
    submodality_id = Column(String(36), ForeignKey("submodalities.id"), nullable=True)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=True)

    status = Column(String(20), nullable=False, default=QuestionStatus.PENDING.value)
    model_response = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    # Relationships
    modality = relationship("Modality")
    submodality = relationship("Submodality")
    category = relationship("Category", back_populates="questions")

    # New relationship with vector embeddings
    embeddings = relationship(
        "ChunkEmbedding",
        back_populates="question",
        cascade="all, delete-orphan",
        lazy="select"
    )

    def __repr__(self):
        return f"<Question(id={self.id}, status={self.status})>"

    @property
    def hierarchy_level(self):
        """Returns the level of specificity: 'modality', 'submodality', or 'category'"""
        if self.category_id:
            return "category"
        elif self.submodality_id:
            return "submodality"
        else:
            return "modality"

    @property
    def full_path(self):
        """Returns the full path based on the hierarchy level"""
        try:
            if self.category:
                return self.category.full_path
            elif self.submodality:
                return self.submodality.full_path
            elif self.modality:
                return self.modality.slug
            return None
        except Exception as e:
            logging.exception(f"Error in full_path: {e}")
            return None

    @property
    def full_name(self):
        """Returns the full name with hierarchy"""
        try:
            if self.category:
                return self.category.full_name
            elif self.submodality:
                return self.submodality.full_name
            elif self.modality:
                return self.modality.name
            return None
        except Exception as e:
            logging.exception(f"Error in full_name: {e}")
            return None
