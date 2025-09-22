"""
Model for Modalities
"""

from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base
import uuid


class Modality(Base):
    """
    Model for Modalities
    Modality → Submodality → Category → Question
    """
    __tablename__ = "modalities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    # Relationships
    submodalities = relationship("Submodality", back_populates="modality", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Modality(name='{self.name}', slug='{self.slug}')>"

    @property
    def total_submodalities(self):
        """Returns the total number of submodalities"""
        return len(self.submodalities)

    @property
    def total_categories(self):
        """Returns the total number of categories in all submodalities"""
        total = 0
        for submodality in self.submodalities:
            total += len(submodality.categories)
        return total

    @property
    def total_questions(self):
        """Returns the total number of questions in all submodalities"""
        total = 0
        for submodality in self.submodalities:
            total += submodality.total_questions
        return total
