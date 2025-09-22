"""
Service for generating and managing vector embeddings
Using sentence-transformers with all-MiniLM-L6-v2 model
Optimized for high concurrency with caching and pooling
"""

import asyncio
import logging
import threading
import time
from typing import List, Tuple, Dict, Any
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sentence_transformers import SentenceTransformer

from ..models.chunk_embedding import ChunkEmbedding
from ..config import settings
from ..db.session import get_session

logger = logging.getLogger(__name__)

# Thread pool for embedding operations
_embedding_executor = None
_embedding_executor_lock = threading.Lock()

def get_embedding_executor() -> ThreadPoolExecutor:
    """Get the thread pool for embeddings (singleton)"""
    global _embedding_executor
    if _embedding_executor is None:
        with _embedding_executor_lock:
            if _embedding_executor is None:
                _embedding_executor = ThreadPoolExecutor(
                    max_workers=settings.max_concurrent_embeddings,
                    thread_name_prefix="embedding_worker"
                )
                logger.info(f"Inicializado ThreadPoolExecutor con {settings.max_concurrent_embeddings} workers")
    return _embedding_executor


class EmbeddingService:
    """
    Service for generating and managing vector embeddings
    Usando sentence-transformers con all-MiniLM-L6-v2
    Optimized for high concurrency with caching and pooling
    """
    
    def __init__(self):
        self.model_name = "all-MiniLM-L6-v2"
        self.model = None
        self.dimension = 384  # Dimension of the all-MiniLM-L6-v2 model
        self.batch_size = settings.max_embedding_batch_size
        self._model_lock = threading.Lock()
        self._cache = {}  # Simple cache for frequent embeddings
        self._cache_lock = threading.Lock()
        
    def _load_model(self):
        """Load the sentence-transformers model in a thread-safe way"""
        if self.model is None:
            with self._model_lock:
                if self.model is None:  # Double-check locking
                    logger.info(f"Loading model {self.model_name}...")
                    start_time = time.time()
                    self.model = SentenceTransformer(self.model_name)
                    load_time = time.time() - start_time
                    logger.info(f"Model {self.model_name} loaded successfully in {load_time:.2f}s")
    
    @lru_cache(maxsize=settings.embedding_cache_size)
    def _get_cached_embedding(self, text_hash: str, text: str) -> List[float]:
        """Cache LRU for frequent embeddings"""
        self._load_model()
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
        
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for a given text using all-MiniLM-L6-v2
        Optimized with caching and thread pooling
        
        Args:
            text: Text to generate embedding
            
        Returns:
            List of floats representing the embedding
        """
        try:
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()

            executor = get_embedding_executor()
            loop = asyncio.get_event_loop()

            embedding = await loop.run_in_executor(
                executor,
                self._get_cached_embedding,
                text_hash,
                text
            )
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding for text hash {text_hash[:8]}: {e}")
            raise
    
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch using all-MiniLM-L6-v2
        
        Args:
            texts: List of texts
            
        Returns:
            List of embeddings
        """
        try:
            self._load_model()

            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self.model.encode(texts, convert_to_numpy=True, batch_size=self.batch_size)
            )

            return [embedding.tolist() for embedding in embeddings]
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Divide a text into chunks with overlap
        
        Args:
            text: Text to divide
            chunk_size: Maximum size of the chunk
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size

            if end < len(text):
                last_space = text.rfind(' ', start, end)
                last_period = text.rfind('.', start, end)
                
                cut_point = max(last_space, last_period)
                if cut_point > start:
                    end = cut_point + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap if end < len(text) else end
        
        return chunks
    
    async def create_embedding_for_question_text(
        self,
        question_id: str,
        question_text: str,
        session: AsyncSession
    ) -> ChunkEmbedding:
        """
        Create an embedding directly from the question text (without chunking)
        
        Args:
            question_id: ID of the question
            question_text: Text of the question
            session: Database session
            
        Returns:
            Created ChunkEmbedding
        """
        try:
            embedding = await self.generate_embedding(question_text)

            chunk_embedding = ChunkEmbedding.create_from_text(
                question_id=question_id,
                chunk_text=question_text,
                embedding=embedding,
                chunk_index=0,
                chunk_metadata='{"source": "question_text", "type": "single_chunk"}',
                processing_model="all-MiniLM-L6-v2"
            )
            
            session.add(chunk_embedding)
            await session.flush()
            await session.commit()
            
            logger.info(f"Created embedding for question {question_id}")
            return chunk_embedding
            
        except Exception as e:
            logger.error(f"Error creating embedding for question {question_id}: {e}")
            raise
    
    async def recreate_embedding_for_question_text(
        self,
        question_id: str,
        question_text: str,
        session: AsyncSession
    ) -> ChunkEmbedding:
        """
        Recreate embeddings for a question (delete existing and create new)
        
        Args:
            question_id: ID of the question
            question_text: New text of the question
            session: Database session
            
        Returns:
            Created ChunkEmbedding
        """
        try:
            print(f"🗑️  Deleting existing embeddings for question {question_id}")

            from sqlalchemy import delete
            delete_stmt = delete(ChunkEmbedding).where(ChunkEmbedding.question_id == question_id)
            result = await session.execute(delete_stmt)
            deleted_count = result.rowcount
            
            print(f"✅ {deleted_count} existing embeddings deleted")

            print(f"🔄 Creating new embeddings for updated question")

            embedding = await self.generate_embedding(question_text)

            chunk_embedding = ChunkEmbedding.create_from_text(
                question_id=question_id,
                chunk_text=question_text,
                embedding=embedding,
                chunk_index=0,
                chunk_metadata='{"source": "question_text", "type": "single_chunk"}',
                processing_model="all-MiniLM-L6-v2"
            )
            
            session.add(chunk_embedding)
            await session.flush()
            
            new_embedding = chunk_embedding
            
            print(f"✅ New embeddings created successfully")
            return new_embedding
            
        except Exception as e:
            logger.error(f"Error recreating embedding for question {question_id}: {e}")
            raise
    
    async def create_embeddings_for_question(
        self, 
        question_id: str, 
        text: str,
        session: AsyncSession = None
    ) -> List[ChunkEmbedding]:
        """
        Create embeddings for a question dividing the text into chunks
        
        Args:
            question_id: ID of the question
            text: Text to process
            session: Database session (optional)
            
        Returns:
            List of created ChunkEmbedding
        """
        async def _create_embeddings(session: AsyncSession):
            chunks = self.chunk_text(text)
            logger.info(f"Created {len(chunks)} chunks for question {question_id}")

            embeddings = await self.generate_embeddings_batch(chunks)

            chunk_embeddings = []
            for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_embedding = ChunkEmbedding.create_from_text(
                    question_id=question_id,
                    chunk_text=chunk_text,
                    embedding=embedding,
                    chunk_index=i,
                    metadata=f'{{"chunk_count": {len(chunks)}, "total_length": {len(text)}}}'
                )
                session.add(chunk_embedding)
                chunk_embeddings.append(chunk_embedding)
            
            await session.commit()
            logger.info(f"Created {len(chunk_embeddings)} embeddings for question {question_id}")
            
            return chunk_embeddings
        
        if session:
            return await _create_embeddings(session)
        else:
            async with get_session() as session:
                return await _create_embeddings(session)
    
    async def similarity_search(
        self,
        query_embedding: List[float],
        limit: int = 5,
        similarity_threshold: float = 0.7,
        session: AsyncSession = None
    ) -> List[Tuple[ChunkEmbedding, float, Dict[str, Any]]]:
        """
        Search similar embeddings using cosine distance
        
        Args:
            query_embedding: Embedding of the query
            limit: Maximum number of results
            similarity_threshold: Minimum similarity threshold
            session: Database session
            
        Returns:
            List of tuples (ChunkEmbedding, similarity_score, question_data)
        """
        async def _search(session: AsyncSession):
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

            sql = text("""
                SELECT
                    ce.id,
                    ce.question_id,
                    ce.chunk_text,
                    ce.chunk_index,
                    ce.created_at,
                    q.question_text,
                    q.model_response,
                    q.status,
                    1 - (ce.embedding <=> :query_embedding) as similarity
                FROM chunk_embeddings ce
                INNER JOIN questions q ON ce.question_id = q.id
                WHERE 1 - (ce.embedding <=> :query_embedding) >= :threshold
                AND q.status = 'APPROVED'
                ORDER BY ce.embedding <=> :query_embedding
                LIMIT :limit
            """)
            
            result = await session.execute(
                sql,
                {
                    "query_embedding": embedding_str,
                    "threshold": similarity_threshold,
                    "limit": limit
                }
            )
            
            results = []
            for row in result:
                chunk_embedding = ChunkEmbedding(
                    id=row.id,
                    question_id=row.question_id,
                    chunk_text=row.chunk_text,
                    chunk_index=row.chunk_index,
                    created_at=row.created_at
                )

                question_data = {
                    'question_text': row.question_text,
                    'model_response': row.model_response,
                    'status': row.status
                }
                
                results.append((chunk_embedding, float(row.similarity), question_data))
            
            return results
        
        if session:
            return await _search(session)
        else:
            async with get_session() as session:
                return await _search(session)
    
    async def search_by_text(
        self,
        query_text: str,
        limit: int = 5,
        similarity_threshold: float = 0.7,
        session: AsyncSession = None
    ) -> List[Tuple[ChunkEmbedding, float, Dict[str, Any]]]:
        """
        Search similar embeddings from a query text
        
        Args:
            query_text: Query text
            limit: Maximum number of results
            similarity_threshold: Minimum similarity threshold
            session: Database session
            
        Returns:
            List of tuples (ChunkEmbedding, similarity_score, question_data)
        """
        query_embedding = await self.generate_embedding(query_text)

        return await self.similarity_search(
            query_embedding=query_embedding,
            limit=limit,
            similarity_threshold=similarity_threshold,
            session=session
        )
    
    async def get_question_embeddings(
        self,
        question_id: str,
        session: AsyncSession = None
    ) -> List[ChunkEmbedding]:
        """
        Get all embeddings for a specific question
        
        Args:
            question_id: ID of the question
            session: Database session
            
        Returns:
            List of ChunkEmbedding
        """
        async def _get_embeddings(session: AsyncSession):
            stmt = select(ChunkEmbedding).where(
                ChunkEmbedding.question_id == question_id
            ).order_by(ChunkEmbedding.chunk_index)
            
            result = await session.execute(stmt)
            return result.scalars().all()
        
        if session:
            return await _get_embeddings(session)
        else:
            async with get_session() as session:
                return await _get_embeddings(session)
    
    async def delete_question_embeddings(
        self,
        question_id: str,
        session: AsyncSession = None
    ) -> int:
        """
        Delete all embeddings for a question
        
        Args:
            question_id: ID of the question
            session: Database session
            
        Returns:
            Number of embeddings deleted
        """
        async def _delete_embeddings(session: AsyncSession):
            stmt = select(ChunkEmbedding).where(
                ChunkEmbedding.question_id == question_id
            )
            result = await session.execute(stmt)
            embeddings = result.scalars().all()
            
            count = len(embeddings)
            for embedding in embeddings:
                await session.delete(embedding)
            
            await session.commit()
            return count
        
        if session:
            return await _delete_embeddings(session)
        else:
            async with get_session() as session:
                return await _delete_embeddings(session)


embedding_service = EmbeddingService()
