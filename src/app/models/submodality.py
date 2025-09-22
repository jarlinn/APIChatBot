"""
Model for Submodalities
"""

from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base
import uuid


class Submodality(Base):
    """
    Model for Submodalities
    Modality → Submodality → Category → Question
    """
    __tablename__ = "submodalities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    modality_id = Column(String(36), ForeignKey("modalities.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    # Relationships
    modality = relationship("Modality", back_populates="submodalities")
    categories = relationship("Category", back_populates="submodality", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Submodality(name='{self.name}', modality='{self.modality.name if self.modality else 'None'}')>"

    @property
    def full_name(self):
        """Returns the full name with the modality"""
        if self.modality:
            return f"{self.modality.name} > {self.name}"
        return self.name

    @property
    def full_path(self):
        """Returns the full path (modalidad/submodalidad)"""
        if self.modality:
            return f"{self.modality.slug}/{self.slug}"
        return self.slug

    @property
    def total_categories(self):
        """Returns the total number of categories"""
        return len(self.categories)

    @property
    def total_questions(self):
        """Returns the total number of questions in all categories"""
        total = 0
        for category in self.categories:
            total += len(category.questions)
        return total
