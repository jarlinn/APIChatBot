"""
Schemas for Document
"""

from typing import Optional, List, Generic, TypeVar
from enum import Enum
from pydantic import BaseModel, Field, field_validator

T = TypeVar('T')


class DocumentStatus(str, Enum):
    """Schema for document status"""
    APPROVED = "APPROVED"
    DISABLED = "DISABLED"


class DocumentCreate(BaseModel):
    """Schema for creating a document"""
    question_text: str = Field(..., min_length=1, description="Question text")
    # Flexible hierarchy - at least modality is required
    modality_id: str = Field(..., description="ID of the modality (required)")
    submodality_id: Optional[str] = Field(None, description="ID of the submodality (optional)")
    category_id: Optional[str] = Field(None, description="ID of the category (optional)")

    @field_validator("category_id")
    @classmethod
    def validate_hierarchy(cls, v, info):
        """Validate hierarchy logic"""
        if v and not info.data.get("submodality_id"):
            raise ValueError("submodality_id is required when category_id is provided")
class DocumentApprovalRequest(BaseModel):
    """Schema for approval request"""
    action: str = Field(..., description="Action to perform: 'approve' or 'disable'")

    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        """Validate action"""
        if v not in ["approve", "disable"]:
            raise ValueError('action must be "approve" or "disable"')
        return v


class DocumentUpdate(BaseModel):
    """Schema for updating a document"""
    question_text: Optional[str] = Field(None, min_length=1, description="Question text")
    modality_id: Optional[str] = Field(None, description="ID of the modality")
    submodality_id: Optional[str] = Field(None, description="ID of the submodality")
    category_id: Optional[str] = Field(None, description="ID of the category")

    @field_validator("category_id")
    @classmethod
    def validate_hierarchy(cls, v, info):
        """Validate hierarchy logic"""
        if v and not info.data.get("submodality_id"):
            raise ValueError("submodality_id is required when category_id is provided")
        return v


        return v


class DocumentResponse(BaseModel):
    """Schema for document response"""
    document_id: str
    status: str
    question_text: str
    file_path: str
    file_name: Optional[str] = None
    file_type: Optional[str] = None

    # Flexible hierarchy fields
    modality_id: str
    modality_name: Optional[str] = None
    submodality_id: Optional[str] = None
    submodality_name: Optional[str] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None

    # Computed hierarchy fields
    hierarchy_level: Optional[str] = None  # 'modality', 'submodality', or 'category'
    full_name: Optional[str] = None
    full_path: Optional[str] = None
    created_at: str


class PaginationInfo(BaseModel):
    """Schema for pagination information"""

    page: int = Field(..., description="Current page (starting at 1)")
    page_size: int = Field(..., description="Number of elements per page")
    total_items: int = Field(..., description="Total number of elements")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="If there is a next page")
    has_previous: bool = Field(..., description="If there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Schema for paginated response"""

    items: List[T] = Field(..., description="List of elements")
    pagination: PaginationInfo = Field(..., description="Pagination information")


class PaginatedDocumentResponse(BaseModel):
    """Schema for paginated document response"""

    items: List[DocumentResponse] = Field(..., description="List of documents")
    pagination: PaginationInfo = Field(..., description="Pagination information")


class SimilaritySearchRequest(BaseModel):
    """Schema for similarity search request"""

    question_text: str = Field(
        ..., min_length=1, description="Question text to search for similarities"
    )
    similarity_threshold: Optional[float] = Field(
        0.8, ge=0.0, le=1.0, description="Minimum similarity threshold (0.0 a 1.0)"
    )
    limit: Optional[int] = Field(
        5, ge=1, le=20, description="Maximum number of similar results"
    )


class SimilarDocumentResponse(BaseModel):
    """Schema for similar document response"""

    chunk_id: str = Field(..., description="ID of the chunk embedding")
    document_id: str = Field(..., description="ID of the associated document")
    chunk_text: str = Field(..., description="Similar chunk text")
    similarity_score: float = Field(
        ..., description="Similarity score (0.0 a 1.0)"
    )
    chunk_index: int = Field(
        ..., description="Index of the chunk in the original document"
    )
    created_at: str = Field(..., description="Creation date of the embedding")
    # Additional fields from the document
    document_question_text: Optional[str] = Field(
        None, description="Original document question text"
    )
    document_file_url: Optional[str] = Field(
        None, description="Signed URL to download the document file (valid for 24 hours)"
    )


class SimilaritySearchResponse(BaseModel):
    """Schema for similarity search response"""

    query_text: str = Field(..., description="Original query text")
    found_similarities: bool = Field(..., description="If similarities were found")
    message: str = Field(..., description="Descriptive message of the result")
    similar_chunks: List[SimilarDocumentResponse] = Field(
        default=[], description="List of similar chunks found"
    )
    total_found: int = Field(..., description="Total number of similarities found")