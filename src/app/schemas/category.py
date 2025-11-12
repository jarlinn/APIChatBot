"""
Schemas for Category
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, model_validator


class CategoryBase(BaseModel):
    """Schema base for Category"""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the category")
    slug: str = Field(..., min_length=1, max_length=255, description="Slug of the category")
    description: Optional[str] = Field(None, description="Description of the category")
    modality_id: Optional[str] = Field(None, description="ID of the parent modality (if direct)")
    submodality_id: Optional[str] = Field(None, description="ID of the parent submodality")


class CategoryCreate(BaseModel):
    """Schema for creating a category"""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the category")
    description: Optional[str] = Field(None, description="Description of the category")
    modality_id: Optional[str] = Field(None, description="ID of the parent modality (if direct)")
    submodality_id: Optional[str] = Field(None, description="ID of the parent submodality")

    @model_validator(mode='after')
    def check_parent(self):
        if not self.modality_id and not self.submodality_id:
            raise ValueError("Either modality_id or submodality_id must be provided")
        return self


class CategoryUpdate(BaseModel):
    """Schema for updating a category"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Name of the category")
    description: Optional[str] = Field(None, description="Description of the category")
    modality_id: Optional[str] = Field(None, description="ID of the parent modality (if direct)")
    submodality_id: Optional[str] = Field(None, description="ID of the parent submodality")


class CategoryResponse(CategoryBase):
    """Schema for category response"""
    id: str = Field(..., description="Unique ID of the category")
    created_at: datetime = Field(..., description="Creation date")
    updated_at: Optional[datetime] = Field(None, description="Last update date")

    # Hierarchy information
    submodality_name: Optional[str] = Field(None, description="Name of the submodality")
    modality_name: Optional[str] = Field(None, description="Name of the modality")
    full_name: str = Field(..., description="Full name with hierarchy")
    full_path: str = Field(..., description="Full path")

    # Statistics
    total_questions: int = Field(0, description="Total number of questions")

    class Config:
        from_attributes = True


class CategoryWithQuestions(CategoryResponse):
    """Schema for category with its questions"""
    questions: List["QuestionResponse"] = Field(default_factory=list, description="List of questions")

# To avoid circular imports
from .question import QuestionResponse
CategoryWithQuestions.model_rebuild()
