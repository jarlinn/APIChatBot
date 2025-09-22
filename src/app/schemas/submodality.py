"""
Schemas for Submodality
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class SubmodalityBase(BaseModel):
    """Schema base for Submodality"""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the submodality")
    slug: str = Field(..., min_length=1, max_length=255, description="Slug of the submodality")
    description: Optional[str] = Field(None, description="Description of the submodality")
    modality_id: str = Field(..., description="ID of the parent modality")


class SubmodalityCreate(BaseModel):
    """Schema for creating a submodality"""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the submodality")
    description: Optional[str] = Field(None, description="Description of the submodality")
    modality_id: str = Field(..., description="ID of the parent modality")


class SubmodalityUpdate(BaseModel):
    """Schema for updating a submodality"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Name of the submodality")
    description: Optional[str] = Field(None, description="Description of the submodality")
    modality_id: Optional[str] = Field(None, description="ID of the parent modality")


class SubmodalityResponse(SubmodalityBase):
    """Schema for submodality response"""
    id: str = Field(..., description="Unique ID of the submodality")
    created_at: datetime = Field(..., description="Creation date")
    updated_at: Optional[datetime] = Field(None, description="Last update date")

    # Parent modality information
    modality_name: Optional[str] = Field(None, description="Name of the parent modality")
    full_name: str = Field(..., description="Full name with hierarchy")
    full_path: str = Field(..., description="Full path")

    # Statistics
    total_categories: int = Field(0, description="Total number of categories")
    total_questions: int = Field(0, description="Total number of questions")

    class Config:
        from_attributes = True


class SubmodalityWithCategories(SubmodalityResponse):
    """Schema for submodality with its categories"""
    categories: List["CategoryResponse"] = Field(default_factory=list, description="List of categories")

# To avoid circular imports
from .category import CategoryResponse
SubmodalityWithCategories.model_rebuild()
