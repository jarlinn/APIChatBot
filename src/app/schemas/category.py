from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Nombre de la categoría")
    slug: Optional[str] = Field(None, min_length=1, max_length=255, description="Slug único de la categoría (se genera automáticamente si no se proporciona)")
    description: Optional[str] = Field(None, description="Descripción de la categoría")
    parent_id: Optional[str] = Field(None, description="ID de la categoría padre")
    is_active: Optional[bool] = Field(True, description="Si la categoría está activa")

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: Optional[bool] = None

class CategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    level: int
    is_active: bool
    full_path: str
    display_name: str
    children_count: Optional[int] = None
    questions_count: Optional[int] = None

class CategoryTree(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    level: int
    is_active: bool
    full_path: str
    children: List['CategoryTree'] = []
    questions_count: int = 0

# Para evitar problemas de referencia circular
CategoryTree.model_rebuild()
