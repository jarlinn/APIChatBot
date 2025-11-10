"""
Model for storing vector embeddings with pgvector
"""

from sqlalchemy import Column, String, Text, ForeignKey, Integer, DateTime, func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import uuid
from typing import Any, List, Optional, Dict

from ..db.database import Base


class ChunkEmbedding(Base):
    """
    Model for storing vector embeddings of text chunks
    
    This model uses pgvector to store and query embeddings
    efficiently in PostgreSQL
    """
    __tablename__ = "chunk_embeddings"

    id = Column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        comment="Unique identifier of the chunk embedding"
    )

    question_id = Column(
        String(36),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="ID of the associated question"
    )

    document_id = Column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="ID of the associated document"
    )

    chunk_text = Column(
        Text,
        nullable=False,
        comment="Processed chunk text"
    )

    # Embedding vectorial - MAIN FIELD FOR PGVECTOR
    embedding = Column(
        Vector(384),  # Fixed dimension for all-MiniLM-L6-v2
        nullable=False,
        comment="Vector embedding of 384 dimensions (all-MiniLM-L6-v2)"
    )

    chunk_index = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Index of the chunk within the document"
    )

    chunk_size = Column(
        Integer,
        nullable=True,
        comment="Size of the chunk in characters"
    )

    chunk_metadata = Column(
        Text,
        nullable=True,
        comment="Additional metadata of the chunk in JSON format"
    )

    processing_model = Column(
        String(100),
        nullable=True,
        comment="Model used to generate the embedding"
    )
    
    processing_version = Column(
        String(50),
        nullable=True,
        comment="Version of the processing model"
    )

    similarity_score = Column(
        String(50),
        nullable=True,
        comment="Similarity score (calculated in queries)"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Creation date"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
        comment="Last update date"
    )

    question = relationship(
        "Question",
        back_populates="embeddings",
        lazy="select"
    )

    document = relationship(
        "Document",
        back_populates="embeddings",
        lazy="select"
    )

    def __repr__(self):
        return f"<ChunkEmbedding(id={self.id}, question_id={self.question_id}, chunk_index={self.chunk_index})>"

    @property
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary for serialization"""
        return {
            "id": self.id,
            "question_id": self.question_id,
            "chunk_text": self.chunk_text,
            "chunk_index": self.chunk_index,
            "chunk_size": self.chunk_size,
            "chunk_metadata": self.chunk_metadata,
            "processing_model": self.processing_model,
            "processing_version": self.processing_version,
            "similarity_score": self.similarity_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def create_from_text(
        cls,
        chunk_text: str,
        embedding: List[float],
        question_id: Optional[str] = None,
        document_id: Optional[str] = None,
        chunk_index: int = 0,
        chunk_metadata: Optional[str] = None,
        processing_model: str = "text-embedding-ada-002"
    ) -> "ChunkEmbedding":
        """
        Factory method to create a ChunkEmbedding from text and embedding

        Args:
            chunk_text: Text of the chunk
            embedding: List of floats representing the embedding
            question_id: ID of the associated question
            document_id: ID of the associated document
            chunk_index: Index of the chunk
            chunk_metadata: Additional metadata in JSON
            processing_model: Model used to generate the embedding

        Returns:
            New instance of ChunkEmbedding
        """
        return cls(
            question_id=question_id,
            document_id=document_id,
            chunk_text=chunk_text,
            embedding=embedding,
            chunk_index=chunk_index,
            chunk_size=len(chunk_text),
            chunk_metadata=chunk_metadata,
            processing_model=processing_model,
            processing_version="1.0"
        )
