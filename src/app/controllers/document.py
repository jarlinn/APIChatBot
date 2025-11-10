"""
Controllers for Documents
"""

import math
from typing import Optional
import logging

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, Depends
from fastapi.responses import StreamingResponse

from src.app.db.session import get_async_session
from src.app.models import Document, Category, Modality, Submodality
from src.app.schemas.document import (
    DocumentResponse,
    DocumentUpdate,
    DocumentApprovalRequest,
    PaginatedDocumentResponse,
    PaginationInfo,
    SimilaritySearchRequest,
    SimilaritySearchResponse,
    SimilarDocumentResponse,
)
from src.app.services.storage_service import storage_service
from src.app.services.embedding_service import embedding_service
from src.app.dependencies.auth import get_current_active_user

from ..schemas.document import DocumentStatus

logger = logging.getLogger(__name__)

router = APIRouter()


def build_document_response(document: Document) -> DocumentResponse:
    """Helper to build DocumentResponse with full hierarchy information"""
    return DocumentResponse(
        document_id=str(document.id),
        status=document.status,
        question_text=document.question_text,
        file_path=document.file_path,
        file_name=document.file_name,
        file_type=document.file_type,
        # Flexible hierarchy fields (required modality, optional submodality/category)
        modality_id=str(document.modality_id),
        modality_name=document.modality.name if document.modality else None,
        submodality_id=(
            str(document.submodality_id) if document.submodality_id else None
        ),
        submodality_name=document.submodality.name if document.submodality else None,
        category_id=str(document.category_id) if document.category_id else None,
        category_name=document.category.name if document.category else None,
        # Computed hierarchy fields
        hierarchy_level=document.hierarchy_level,
        full_name=document.full_name,
        full_path=document.full_path,
        created_at=str(document.created_at),
    )


@router.post("/documents", response_model=DocumentResponse)
async def create_document(
    question_text: str = Form(...),
    file: UploadFile = File(...),
    modality_id: str = Form(...),
    submodality_id: Optional[str] = Form(None),
    category_id: Optional[str] = Form(None),
    current_user=Depends(get_current_active_user),
):
    """Create document with question_text and file, creates embedding, status DONE by default"""
    file_path = None
    try:
        # Validate file is provided
        if not file:
            raise HTTPException(
                status_code=400,
                detail="File is required",
            )

        # Validate flexible hierarchy
        async for session in get_async_session():
            # Validate modality exists (required)
            modality = await session.get(Modality, modality_id)
            if not modality:
                raise HTTPException(status_code=404, detail="Modality not found")

            # Validate submodality if provided
            submodality = None
            if submodality_id:
                submodality = await session.get(Submodality, submodality_id)
                if not submodality:
                    raise HTTPException(status_code=404, detail="Submodality not found")
                # Validate submodality belongs to modality
                if submodality.modality_id != modality_id:
                    raise HTTPException(
                        status_code=400,
                        detail="Submodality does not belong to the specified modality",
                    )

            # Validate category if provided
            category = None
            if category_id:
                category = await session.get(Category, category_id)
                if not category:
                    raise HTTPException(status_code=404, detail="Category not found")
                # Validate category belongs to submodality (if submodality is specified)
                if submodality_id and category.submodality_id != submodality_id:
                    raise HTTPException(
                        status_code=400,
                        detail="Category does not belong to the specified submodality",
                    )
                # If no submodality specified but category exists, auto-set submodality
                if not submodality_id:
                    submodality_id = category.submodality_id
                    submodality = await session.get(
                        Submodality, category.submodality_id
                    )

        # Upload file to MinIO/S3 (any file type allowed)
        file_path = await storage_service.upload_file(file, "documents")

        # Create document
        async for session in get_async_session():
            doc = Document(
                question_text=question_text,
                file_path=file_path,
                file_name=file.filename,
                file_type=file.content_type,
                modality_id=modality_id,
                submodality_id=submodality_id if submodality_id else None,
                category_id=category_id if category_id else None,
                status=DocumentStatus.APPROVED.value,  # Always APPROVED by default
            )
            session.add(doc)
            await session.commit()  # Commit the document first
            await session.refresh(doc)

            try:
                # Create embedding after document is committed
                await embedding_service.create_embedding_for_document_text(
                    document_id=str(doc.id),
                    question_text=question_text,
                    session=session,
                )
                logger.info(f"Embedding generated for document {doc.id}")

                # Load relationships for response
                await session.refresh(doc, ["modality", "submodality", "category"])
                return build_document_response(doc)
            except Exception as exc:
                # If embedding fails, delete the document to maintain atomicity
                logger.error(f"Error generating embedding for document {doc.id}: {str(exc)}")
                await session.delete(doc)
                await session.commit()
                # Also delete the uploaded file if it exists
                raise HTTPException(
                    status_code=500,
                    detail=f"Error generating embedding: {str(exc)}. The document was not created."
                )
    except HTTPException as http_err:
        try:
            if file_path:
                await storage_service.delete_file(file_path)
        except Exception as exc_file:
            logger.error(f"Error deleting file {file_path}: {exc_file}")
        raise http_err
    except Exception as exc:
        try:
            if file_path:
                await storage_service.delete_file(file_path)
        except Exception as exc_file:
            logger.error(f"Error deleting file {file_path}: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating document: {str(exc)}. The document was not created."
        )


@router.get("/documents", response_model=PaginatedDocumentResponse)
async def get_documents(
    page: int = Query(1, ge=1, description="Number of page (starting at 1)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Elements per page (maximum 100)"
    ),
    modality_id: Optional[str] = Query(None, description="Filter by modality"),
    submodality_id: Optional[str] = Query(None, description="Filter by submodality"),
    category_id: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status (APPROVED, DISABLED)"),
    search: Optional[str] = Query(None, description="Search in question text"),
    current_user=Depends(get_current_active_user),
):
    """Get paginated list of documents with optional filters"""
    async for session in get_async_session():
        # Load all relationships for flexible hierarchy
        query = select(Document).options(
            selectinload(Document.modality),
            selectinload(Document.submodality),
            selectinload(Document.category),
        )

        # Flexible hierarchy filtering
        if modality_id:
            query = query.where(Document.modality_id == modality_id)
        if submodality_id:
            query = query.where(Document.submodality_id == submodality_id)
        if category_id:
            query = query.where(Document.category_id == category_id)

        if status:
            query = query.where(Document.status == status)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Document.question_text.ilike(search_term))
            )

        count_query = select(func.count(Document.id))
        # Apply same filters to count query
        if modality_id:
            count_query = count_query.where(Document.modality_id == modality_id)
        if submodality_id:
            count_query = count_query.where(Document.submodality_id == submodality_id)
        if category_id:
            count_query = count_query.where(Document.category_id == category_id)
        if status:
            count_query = count_query.where(Document.status == status)
        if search:
            search_term = f"%{search}%"
            count_query = count_query.where(
                (Document.question_text.ilike(search_term))
            )

        total_count_result = await session.execute(count_query)
        total_items = total_count_result.scalar()

        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
        offset = (page - 1) * page_size

        query = query.order_by(Document.created_at.desc())
        query = query.offset(offset).limit(page_size)

        result = await session.execute(query)
        documents = result.scalars().all()

        response_documents = []
        for doc in documents:
            response_documents.append(build_document_response(doc))

        pagination_info = PaginationInfo(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )

        return PaginatedDocumentResponse(
            items=response_documents, pagination=pagination_info
        )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, current_user=Depends(get_current_active_user)):
    """Get a specific document by ID"""
    async for session in get_async_session():
        result = await session.execute(
            select(Document)
            .where(Document.id == document_id)
            .options(
                selectinload(Document.modality),
                selectinload(Document.submodality),
                selectinload(Document.category),
            )
        )
        document = result.scalar_one_or_none()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return build_document_response(document)


@router.get("/documents/{document_id}/file")
async def get_document_file(
    document_id: str, current_user=Depends(get_current_active_user)
):
    """Endpoint to download the file of a document"""
    async for session in get_async_session():
        document = await session.get(Document, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if not document.file_path:
            raise HTTPException(
                status_code=404, detail="No file associated with this document"
            )

        if not storage_service.file_exists(document.file_path):
            raise HTTPException(status_code=404, detail="File not found in the server")

        try:
            file_stream = storage_service.get_file_stream(document.file_path)

            return StreamingResponse(
                file_stream,
                media_type=document.file_type or "application/octet-stream",
                headers={
                    "Content-Disposition": (
                        f"attachment; filename={document.file_name or 'document'}"
                    )
                },
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error downloading file: {str(e)}"
            )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str, current_user=Depends(get_current_active_user)
):
    """Delete a document completely from database and associated files"""
    async for session in get_async_session():
        result = await session.execute(
            select(Document)
            .where(Document.id == document_id)
            .options(
                selectinload(Document.modality),
                selectinload(Document.submodality),
                selectinload(Document.category),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete associated file from MinIO if exists
        if document.file_path:
            try:
                await storage_service.delete_file(document.file_path)
                logger.info(f"File deleted from MinIO: {document.file_path}")
            except Exception as e:
                logger.error(f"Error deleting file {document.file_path}: {e}")
                # Continue with document deletion even if file deletion fails

        # Delete document from database
        await session.delete(document)
        await session.commit()

        logger.info(f"Document {document_id} completely deleted from database")

        return {"message": f"Document {document_id} successfully deleted"}
@router.patch("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    question_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    modality_id: Optional[str] = Form(None),
    submodality_id: Optional[str] = Form(None),
    category_id: Optional[str] = Form(None),
    current_user=Depends(get_current_active_user),
):
    """Update document (question_text, file and/or hierarchy)"""
    new_file_path = None
    try:
        async for session in get_async_session():
            # Buscar el documento existente
            result = await session.execute(
                select(Document)
                .where(Document.id == document_id)
                .options(
                    selectinload(Document.modality),
                    selectinload(Document.submodality),
                    selectinload(Document.category),
                )
            )
            document = result.scalar_one_or_none()

            if not document:
                raise HTTPException(status_code=404, detail="Document not found")

            original_question_text = document.question_text
            original_modality_id = str(document.modality_id or None)
            original_submodality_id = str(document.submodality_id or None)
            original_category_id = str(document.category_id or None)

            # Procesar nuevo archivo si se proporciona
            if file:
                # Subir el nuevo archivo
                new_file_path = await storage_service.upload_file(file, "documents")
                # Eliminar el archivo anterior si existe
                if document.file_path:
                    try:
                        await storage_service.delete_file(document.file_path)
                        logger.info(f"Old file deleted: {document.file_path}")
                    except Exception as e:
                        logger.error(f"Error deleting old file {document.file_path}: {e}")
                        # Continue with update even if old file deletion fails

                # Actualizar campos del archivo
                document.file_path = new_file_path
                document.file_name = file.filename
                document.file_type = file.content_type
                logger.info(f"New file uploaded for document {document_id}: {new_file_path}")

            # Actualizar campos si se proporcionan
            if question_text is not None:
                document.question_text = question_text

            hierarchy_changed = False

            # Validar y actualizar jerarquía si se proporciona
            if modality_id and modality_id.strip():
                modality = await session.get(Modality, modality_id)
                if not modality:
                    raise HTTPException(status_code=404, detail="Modality not found")
                if original_modality_id != modality_id:
                    document.modality_id = modality_id
                    # Cuando cambia la modalidad, null submodality y category
                    document.submodality_id = None
                    document.category_id = None
                    hierarchy_changed = True
                    logger.info(f"Modality changed to {modality_id}, nulled submodality and category")

            # Validar y actualizar submodality si se proporciona
            if submodality_id and submodality_id.strip():
                submodality = await session.get(Submodality, submodality_id)
                if not submodality:
                    raise HTTPException(status_code=404, detail="Submodality not found")
                # Validar que pertenece a la modalidad actual
                current_modality_id = document.modality_id
                if submodality.modality_id != current_modality_id:
                    raise HTTPException(
                        status_code=400,
                        detail="Submodality does not belong to the current modality",
                    )
                if original_submodality_id != submodality_id:
                    document.submodality_id = submodality_id
                    # Cuando cambia submodality, null category (solo si modality no cambió)
                    if not hierarchy_changed:  # Solo null category si modality no cambió
                        document.category_id = None
                        logger.info(f"Submodality changed to {submodality_id}, nulled category")
                    hierarchy_changed = True

            # Validar y actualizar category si se proporciona
            if category_id and category_id not in ("", "null") and category_id.strip():
                category = await session.get(Category, category_id)
                if not category:
                    raise HTTPException(status_code=404, detail="Category not found")
                # Validar que pertenece a la submodality actual
                current_submodality_id = document.submodality_id
                if current_submodality_id and category.submodality_id != current_submodality_id:
                    raise HTTPException(
                        status_code=400,
                        detail="Category does not belong to the current submodality",
                    )
                # Si no hay submodality pero existe category, auto-set submodality
                if not current_submodality_id and category.submodality_id:
                    document.submodality_id = category.submodality_id
                    logger.info(f"Auto-set submodality to {category.submodality_id} for category {category_id}")
                if original_category_id != category_id:
                    document.category_id = category_id
                    hierarchy_changed = True

            # Regenerar embeddings solo si question_text cambió
            if (
                question_text is not None
                and document.question_text != original_question_text
            ):
                logger.info(f"Regenerating embeddings for updated document...")
                try:
                    await embedding_service.recreate_embedding_for_document_text(
                        document_id=document_id,
                        question_text=document.question_text,
                        session=session,
                    )
                    logger.info(f"Embeddings regenerated for document {document_id}")
                except Exception as exc:
                    logger.error(
                        f"Error generating embedding for document {document_id}: {str(exc)}"
                    )
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error generating embedding: {str(exc)}. The document was not updated."
                    )

            await session.commit()

            # Reload document with all nested relationships
            result = await session.execute(
                select(Document)
                .where(Document.id == document_id)
                .options(
                    selectinload(Document.modality),
                    selectinload(Document.submodality),
                    selectinload(Document.category)
                )
            )
            document = result.scalar_one()

            return build_document_response(document)

    except HTTPException:
        # Si hay error y se subió un nuevo archivo, eliminarlo
        if new_file_path:
            try:
                await storage_service.delete_file(new_file_path)
            except Exception as e:
                logger.error(f"Error deleting new file {new_file_path}: {e}")
        raise
    except Exception as e:
        # Si hay error y se subió un nuevo archivo, eliminarlo
        if new_file_path:
            try:
                await storage_service.delete_file(new_file_path)
            except Exception as e:
                logger.error(f"Error deleting new file {new_file_path}: {e}")
        logger.error(f"Error in update_document: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.patch("/documents/{document_id}/approval", response_model=DocumentResponse)
async def update_document_approval(
    document_id: str,
    approval_request: DocumentApprovalRequest,
    current_user=Depends(get_current_active_user),
):
    """Approve or disable a document"""
    async for session in get_async_session():
        result = await session.execute(
            select(Document)
            .where(Document.id == document_id)
            .options(
                selectinload(Document.modality),
                selectinload(Document.submodality),
                selectinload(Document.category),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if approval_request.action == "approve":
            document.status = DocumentStatus.APPROVED.value
        elif approval_request.action == "disable":
            document.status = DocumentStatus.DISABLED.value

        await session.commit()
        await session.refresh(document)

        return build_document_response(document)




@router.post("/search-documents-similarity", response_model=SimilaritySearchResponse)
async def search_documents_similarity(
    request: SimilaritySearchRequest,
    session=Depends(get_async_session),
    # current_user=Depends(get_current_active_user),
):
    """
    Search for similar documents in the database using vector embeddings.

    This endpoint:
    1. Receives a question text
    2. Generates a vector embedding using the all-MiniLM-L6-v2 model
    3. Searches in the chunk_embeddings table using cosine similarity with pgvector
    4. Returns the similar documents found or a message indicating that there are no similarities
    """
    try:
        if not request.question_text.strip():
            raise HTTPException(
                status_code=400, detail="The question text cannot be empty"
            )

        logger.info(f"🔍 Searching for document similarities for: '{request.question_text[:100]}...'")
        logger.info(
            f"Parameters: threshold={request.similarity_threshold}, limit={request.limit}"
        )

        similar_results = await embedding_service.search_by_text_for_documents(
            query_text=request.question_text,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold,
            session=session,
        )

        logger.info(f"Found {len(similar_results)} similar document results")

        if not similar_results:
            return SimilaritySearchResponse(
                query_text=request.question_text,
                found_similarities=False,
                message="No similar documents found with the specified similarity threshold.",
                similar_chunks=[],
                total_found=0,
            )

        similar_chunks = []
        for chunk_embedding, similarity_score, document_data in similar_results:
            # Generate signed URL for the document file
            file_url = None
            if document_data.get("file_path"):
                try:
                    file_url = storage_service.get_file_url(document_data["file_path"], expires_in_hours=24)
                    logger.info(f"Generated signed URL for document {chunk_embedding.document_id}: {file_url[:50]}...")
                except Exception as e:
                    logger.warning(f"Could not generate signed URL for document {chunk_embedding.document_id}: {e}")

            similar_chunk = SimilarDocumentResponse(
                chunk_id=chunk_embedding.id,
                document_id=chunk_embedding.document_id,
                chunk_text=chunk_embedding.chunk_text,
                similarity_score=round(similarity_score, 4),
                chunk_index=chunk_embedding.chunk_index,
                created_at=str(chunk_embedding.created_at),
                document_question_text=document_data.get("question_text"),
                document_file_url=file_url,  # New field
            )
            similar_chunks.append(similar_chunk)

        best_similarity = similar_chunks[0].similarity_score if similar_chunks else 0
        message = f"Found {len(similar_chunks)} similar documents. The best similarity is {best_similarity:.2%}."

        logger.info(f"Document search completed successfully")

        return SimilaritySearchResponse(
            query_text=request.question_text,
            found_similarities=True,
            message=message,
            similar_chunks=similar_chunks,
            total_found=len(similar_chunks),
        )

    except Exception as e:
        logger.error(f"Error in document similarity search: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error internal server during document similarity search: {str(e)}",
        )