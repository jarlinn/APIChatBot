"""
Model for Categories
"""
import logging
from sqlalchemy import Column, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base
import uuid


class Category(Base):
    """
    Model for Categories (lowest level of hierarchy)
    Modality → Submodality → Category → Question
    """
    __tablename__ = "categories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    submodality_id = Column(String(36), ForeignKey("submodalities.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    # Relationships
    submodality = relationship("Submodality", back_populates="categories")
    questions = relationship("Question", back_populates="category")

    def __repr__(self):
        return f"<Category(name='{self.name}', submodality='{self.submodality.name if self.submodality else 'None'}')>"

    @property
    def full_path(self):
        """Returns the full path of the category (modality/submodality/category)"""
        try:
            if self.submodality:
                return f"{self.submodality.full_path}/{self.slug}"
            return self.slug
        except:
            # Fallback si hay algún problema con la relación
            return self.slug

    @property
    def full_name(self):
        """Returns the full name with the hierarchy"""
        try:
            if self.submodality:
                return f"{self.submodality.full_name} > {self.name}"
            return self.name
        except Exception as ex:
            logging.exception(f"Error in full_name: {ex}")
            # Fallback if there is any problem with the relationship
            return self.name

    @property
    def modality(self):
        """Returns the modality through the submodality"""
        try:
            return self.submodality.modality if self.submodality else None
        except Exception as ex:
            logging.exception(f"Error in modality: {ex}")
            # Fallback if there is any problem with the relationship
            return None

    @property
    def total_questions(self):
        """Returns the total number of questions in this category"""
        return len(self.questions)
