"""
Schemas for Embeddings
"""

from datetime import datetime
from typing import List, Optional, Any, Dict

from pydantic import BaseModel, Field


class EmbeddingCreateRequest(BaseModel):
    """Schema for creating embeddings"""
    question_id: str = Field(..., description="ID of the question")
    text: str = Field(..., min_length=1, description="Text to generate embeddings")

    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "123e4567-e89b-12d3-a456-426614174000",
                "text": "This is the context of the question that will be processed to generate embeddings."
            }
        }


class EmbeddingResponse(BaseModel):
    """Schema for embedding response"""
    id: str = Field(..., description="Unique ID of the embedding")
    question_id: str = Field(..., description="ID of the associated question")
    chunk_text: str = Field(..., description="Text of the chunk")
    chunk_index: int = Field(..., description="Index of the chunk")
    chunk_size: Optional[int] = Field(None, description="Size of the chunk in characters")
    metadata: Optional[str] = Field(None, description="Additional metadata in JSON")
    processing_model: Optional[str] = Field(None, description="Model used to generate the embedding")
    created_at: Optional[datetime] = Field(None, description="Creation date")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "emb_123e4567-e89b-12d3-a456-426614174000",
                "question_id": "123e4567-e89b-12d3-a456-426614174000",
                "chunk_text": "This is a fragment of the original text divided into chunks.",
                "chunk_index": 0,
                "chunk_size": 256,
                "metadata": "{\"chunk_count\": 3, \"total_length\": 1024}",
                "processing_model": "text-embedding-ada-002",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


class SimilaritySearchRequest(BaseModel):
    """Schema for similarity search"""
    query_text: str = Field(..., min_length=1, description="Query text")
    limit: int = Field(default=5, ge=1, le=50, description="Maximum number of results")
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold (0-1)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query_text": "How does authentication work in the application?",
                "limit": 5,
                "similarity_threshold": 0.7
            }
        }


class SimilaritySearchResult(BaseModel):
    """Schema for similarity search result"""
    embedding: EmbeddingResponse = Field(..., description="Embedding")
    similarity_score: float = Field(..., description="Similarity score (0-1)")

    class Config:
        json_schema_extra = {
            "example": {
                "embedding": {
                    "id": "emb_123e4567-e89b-12d3-a456-426614174000",
                    "question_id": "123e4567-e89b-12d3-a456-426614174000",
                    "chunk_text": "Authentication is handled using JWT tokens...",
                    "chunk_index": 0,
                    "chunk_size": 256,
                    "metadata": "{\"chunk_count\": 3}",
                    "processing_model": "text-embedding-ada-002",
                    "created_at": "2024-01-15T10:30:00Z"
                },
                "similarity_score": 0.85
            }
        }


class SimilaritySearchResponse(BaseModel):
    """Schema for similarity search response"""
    query_text: str = Field(..., description="Original query text")
    results: List[SimilaritySearchResult] = Field(..., description="Results of the search")
    total_results: int = Field(..., description="Total number of results found")

    class Config:
        json_schema_extra = {
            "example": {
                "query_text": "How does authentication work?",
                "results": [
                    {
                        "embedding": {
                            "id": "emb_123",
                            "question_id": "q_123",
                            "chunk_text": "Authentication is handled using JWT...",
                            "chunk_index": 0,
                            "chunk_size": 256,
                            "metadata": "{}",
                            "processing_model": "text-embedding-ada-002",
                            "created_at": "2024-01-15T10:30:00Z"
                        },
                        "similarity_score": 0.85
                    }
                ],
                "total_results": 1
            }
        }


class EmbeddingStatsResponse(BaseModel):
    """Schema for embedding statistics"""
    total_embeddings: int = Field(..., description="Total number of embeddings in the database")
    unique_questions: int = Field(..., description="Number of questions with embeddings")
    avg_chunks_per_question: float = Field(..., description="Average number of chunks per question")
    processing_models: List[Dict[str, Any]] = Field(..., description="Statistics by model")
    embedding_dimension: int = Field(..., description="Dimension of the embeddings")

    class Config:
        json_schema_extra = {
            "example": {
                "total_embeddings": 150,
                "unique_questions": 25,
                "avg_chunks_per_question": 6.0,
                "processing_models": [
                    {"model": "text-embedding-ada-002", "count": 120},
                    {"model": "text-embedding-3-small", "count": 30}
                ],
                "embedding_dimension": 1536
            }
        }


class ChunkingRequest(BaseModel):
    """Schema for dividing text into chunks"""
    text: str = Field(..., min_length=1, description="Text to divide")
    chunk_size: int = Field(default=1000, ge=100, le=4000, description="Maximum size of the chunk")
    overlap: int = Field(default=200, ge=0, le=500, description="Overlap between chunks")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "This is a long text that will be divided into multiple chunks...",
                "chunk_size": 1000,
                "overlap": 200
            }
        }


class ChunkingResponse(BaseModel):
    """Schema for dividing text into chunks"""
    chunks: List[str] = Field(..., description="Generated chunks")
    total_chunks: int = Field(..., description="Total number of chunks")
    original_length: int = Field(..., description="Length of the original text")

    class Config:
        json_schema_extra = {
            "example": {
                "chunks": [
                    "This is the first chunk of the text...",
                    "This is the second chunk with overlap..."
                ],
                "total_chunks": 2,
                "original_length": 1500
            }
        }


class EmbeddingBatchRequest(BaseModel):
    """Schema for processing multiple texts"""
    texts: List[str] = Field(..., min_items=1, max_items=100, description="List of texts")
    question_ids: Optional[List[str]] = Field(None, description="IDs of corresponding questions")

    class Config:
        json_schema_extra = {
            "example": {
                "texts": [
                    "First text to process",
                    "Second text to process"
                ],
                "question_ids": [
                    "q1_123e4567-e89b-12d3-a456-426614174000",
                    "q2_123e4567-e89b-12d3-a456-426614174000"
                ]
            }
        }


class EmbeddingBatchResponse(BaseModel):
    """Schema for processing multiple texts"""
    processed_count: int = Field(..., description="Number of texts processed")
    total_embeddings_created: int = Field(..., description="Total number of embeddings created")
    processing_time_seconds: float = Field(..., description="Processing time in seconds")
    results: List[EmbeddingResponse] = Field(..., description="List of embeddings created")

    class Config:
        json_schema_extra = {
            "example": {
                "processed_count": 2,
                "total_embeddings_created": 8,
                "processing_time_seconds": 1.5,
                "results": []
            }
        }
