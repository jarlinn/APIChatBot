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
    Model for Categories
    Modality → Submodality → Category → Question
    Or directly: Modality → Category → Question
    """
    __tablename__ = "categories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    modality_id = Column(String(36), ForeignKey("modalities.id"), nullable=True)
    submodality_id = Column(String(36), ForeignKey("submodalities.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    # Relationships
    direct_modality = relationship("Modality")
    submodality = relationship("Submodality", back_populates="categories")
    questions = relationship("Question", back_populates="category")
    documents = relationship("Document", back_populates="category")

    def __repr__(self):
        parent = self.submodality.name if self.submodality else (self.direct_modality.name if self.direct_modality else 'None')
        return f"<Category(name='{self.name}', parent='{parent}')>"

    @property
    def full_path(self):
        """Returns the full path of the category (modality/category or modality/submodality/category)"""
        try:
            if self.submodality:
                return f"{self.submodality.full_path}/{self.slug}"
            elif self.direct_modality:
                return f"{self.direct_modality.slug}/{self.slug}"
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
            elif self.direct_modality:
                return f"{self.direct_modality.name} > {self.name}"
            return self.name
        except Exception as ex:
            logging.exception(f"Error in full_name: {ex}")
            # Fallback if there is any problem with the relationship
            return self.name

    @property
    def modality(self):
        """Returns the modality, either directly or through submodality"""
        try:
            return self.direct_modality or (self.submodality.modality if self.submodality else None)
        except Exception as ex:
            logging.exception(f"Error in modality: {ex}")
            # Fallback if there is any problem with the relationship
            return None

    @property
    def modality_name(self):
        """Returns the name of the modality, either directly or through submodality"""
        modality = self.direct_modality or (self.submodality.modality if self.submodality else None)
        return modality.name if modality else None

    @property
    def submodality_name(self):
        """Returns the name of the submodality if exists"""
        return self.submodality.name if self.submodality else None

    @property
    def total_questions(self):
        """Returns the total number of questions in this category"""
        return len(self.questions)
