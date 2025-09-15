from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base
import uuid

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(String(36), ForeignKey("categories.id"), nullable=True)
    level = Column(Integer, default=0)  # Nivel en la jerarquía (0 = raíz)
    is_active = Column(Boolean, default=True)
    
    # Relaciones
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent")
    questions = relationship("Question", back_populates="category")
    
    def __repr__(self):
        return f"<Category(name='{self.name}', level={self.level})>"
    
    @property
    def full_path(self):
        """Retorna la ruta completa de la categoría (ej: modalidades/proyecto-investigacion)"""
        try:
            if self.parent_id and self.parent:
                return f"{self.parent.full_path}/{self.slug}"
            return self.slug
        except:
            # Fallback si hay algún problema con la relación
            return self.slug
    
    @property
    def display_name(self):
        """Retorna el nombre para mostrar con la jerarquía completa de nombres (ej: 'Modalidades > Proyecto de Investigación')"""
        try:
            names = []
            current = self
            while current:
                names.insert(0, current.name)
                current = current.parent
            return " > ".join(names)
        except:
            # Fallback si hay algún problema con la relación
            return self.name
