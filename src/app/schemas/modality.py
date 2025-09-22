"""
Schemas for Modality
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ModalityBase(BaseModel):
    """Schema base for Modality"""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the modality")
    slug: str = Field(..., min_length=1, max_length=255, description="Unique slug of the modality")
    description: Optional[str] = Field(None, description="Description of the modality")


class ModalityCreate(BaseModel):
    """Schema for creating a modality"""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the modality")
    description: Optional[str] = Field(None, description="Description of the modality")


class ModalityUpdate(BaseModel):
    """Schema for updating a modality"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Name of the modality")
    description: Optional[str] = Field(None, description="Description of the modality")


class ModalityResponse(ModalityBase):
    """Schema for modality response"""
    id: str = Field(..., description="Unique ID of the modality")
    created_at: datetime = Field(..., description="Creation date")
    updated_at: Optional[datetime] = Field(None, description="Last update date")

    # Statistics
    total_submodalities: int = Field(0, description="Total number of submodalities")
    total_categories: int = Field(0, description="Total number of categories")
    total_questions: int = Field(0, description="Total number of questions")

    class Config:
        from_attributes = True


class ModalityWithSubmodalities(ModalityResponse):
    """Schema for modality with its submodalities"""
    submodalities: List["SubmodalityResponse"] = Field(default_factory=list, description="List of submodalities")


# To avoid circular imports
from .submodality import SubmodalityResponse
ModalityWithSubmodalities.model_rebuild()
