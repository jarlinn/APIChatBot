"""
Controllers for Questions
"""

import math
from typing import Optional
import logging

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, Depends
from fastapi.responses import StreamingResponse
from sympy import im

from src.app.db.session import get_async_session
from src.app.models import Question, Category, Modality, Submodality
from src.app.schemas.question import (
    QuestionResponse,
    QuestionApprovalRequest,
    QuestionStatus,
    PaginatedQuestionResponse,
    PaginationInfo,
    SimilaritySearchRequest,
    SimilaritySearchResponse,
    SimilarChunkResponse,
)
from src.app.services.storage_service import storage_service
from src.app.services.embedding_service import embedding_service
from src.app.services.gemini_service import gemini_service
from src.app.dependencies.auth import get_current_active_user
from src.app.config import settings
from src.app.utils.questions_utils import delete_file_if_exists

logger = logging.getLogger(__name__)

router = APIRouter()

N8N_WEBHOOK = settings.n8n_webhook


def build_question_response(question: Question) -> QuestionResponse:
    """Helper to build QuestionResponse with full hierarchy information"""
    return QuestionResponse(
        question_id=str(question.id),
        status=question.status,
        question_text=question.question_text,
        context_type=question.context_type,
        context_text=question.context_text,
        context_file=question.context_file,
        # Flexible hierarchy fields (required modality, optional submodality/category)
        modality_id=str(question.modality_id),
        modality_name=question.modality.name if question.modality else None,
        submodality_id=(
            str(question.submodality_id) if question.submodality_id else None
        ),
        submodality_name=question.submodality.name if question.submodality else None,
        category_id=str(question.category_id) if question.category_id else None,
        category_name=question.category.name if question.category else None,
        # Computed hierarchy fields
        hierarchy_level=question.hierarchy_level,
        full_name=question.full_name,
        full_path=question.full_path,
        model_response=question.model_response,
        response_file=getattr(question, "response_file", None),
        response_file_type=getattr(question, "response_file_type", None),
        response_file_name=getattr(question, "response_file_name", None),
        created_at=str(question.created_at),
    )


@router.post("/questions", response_model=QuestionResponse)
async def create_question(
    question_text: str = Form(...),
    context_type: str = Form(...),
    context_text: Optional[str] = Form(None),
    context_file: Optional[UploadFile] = File(None),
    modality_id: str = Form(...),
    submodality_id: Optional[str] = Form(None),
    category_id: Optional[str] = Form(None),
    current_user=Depends(get_current_active_user),
):
    """Create question using FormData with flexible hierarchy (text or file)"""
    context_file_path = None
    try:
        if context_type == "text" and not context_text:
            raise HTTPException(
                status_code=400,
                detail="context_text is required when context_type is 'text'",
            )

        if context_type == "pdf" and not context_file:
            raise HTTPException(
                status_code=400,
                detail="context_file is required when context_type is 'pdf'",
            )

        if context_file and context_file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="The file must be a PDF")

        # Validate consistency between context_type and context_file
        if context_file and context_type != "pdf":
            raise HTTPException(
                status_code=400,
                detail="If a file is provided, context_type must be 'pdf'",
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
                # Validate category belongs to modality
                if category.modality_id != modality_id:
                    raise HTTPException(
                        status_code=400,
                        detail="Category does not belong to the specified modality",
                    )
                # Validate category belongs to submodality (if both have submodality)
                if submodality_id and category.submodality_id and category.submodality_id != submodality_id:
                    raise HTTPException(
                        status_code=400,
                        detail="Category does not belong to the specified submodality",
                    )
                # If no submodality specified but category has submodality, auto-set submodality
                if not submodality_id and category.submodality_id:
                    submodality_id = category.submodality_id
                    submodality = await session.get(
                        Submodality, category.submodality_id
                    )
            # break

        # Process file if provided
        if context_file:
            # Save file in MinIO/S3
            context_file_path = await storage_service.upload_file(context_file, "pdfs")

        # Generate response with Gemini AI BEFORE creating the question
        # If Gemini is configured and fails, question creation should fail
        logger.info(
            f"Generating answer with Gemini for question: {question_text[:50]}..."
        )

        # Check if Gemini is configured (has a real client, not simulated)
        gemini_configured = gemini_service.client is not None

        if gemini_configured:
            # If Gemini is configured, try to generate response and fail if it doesn't work
            try:
                if context_type == "pdf" and context_file_path:
                    model_response = await gemini_service._generate_with_pdf(
                        question_text, context_file_path, "create"
                    )
                else:
                    prompt = gemini_service._build_prompt(question_text, context_text, context_type, "create")
                    model_response = await gemini_service._generate_with_gemini(prompt)
                logger.info(f"Response generated with real Gemini: {len(model_response)} characters")
            except Exception as e:
                logger.error(f"Error generating response with Gemini configured: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error generating response with Gemini: {str(e)}. The question was not created."
                )
        else:
            # If Gemini is not configured, use simulated response
            model_response = gemini_service._simulate_response(question_text, context_type, "create")
            logger.info(f"Gemini not configured, using simulated response: {len(model_response)} characters")

        async for session in get_async_session():
            q = Question(
                question_text=question_text,
                context_text=context_text,
                context_type=context_type,
                context_file=context_file_path,
                modality_id=modality_id,
                submodality_id=submodality_id,
                category_id=category_id,
                status=QuestionStatus.APPROVED.value,
                model_response=model_response,  # Set the response immediately
            )
            session.add(q)
            await session.commit()  # Commit the question first
            await session.refresh(q)

            try:
                # Create embedding after question is committed
                await embedding_service.create_embedding_for_question_text(
                    question_id=str(q.id),
                    question_text=question_text,
                    session=session,
                )
                logger.info(f"Embedding generated for question {q.id}")

                # Load relationships for response
                await session.refresh(q, ["modality", "submodality", "category"])
                return build_question_response(q)
            except Exception as exc:
                # If embedding fails, delete the question to maintain atomicity
                logger.error(f"Error generating embedding for question {q.id}: {str(exc)}")
                await session.delete(q)
                await session.commit()
                # Also delete the uploaded file if it exists
                raise HTTPException(
                    status_code=500,
                    detail=f"Error generating embedding: {str(exc)}. The question was not created."
                )
    except HTTPException as http_err:
        try:
            delete_file_if_exists(context_file_path)
        except Exception as exc_file:
            logger.error(f"Error deleting PDF file {context_file_path}: {exc_file}")
        raise http_err
    except Exception as exc:
        try:
            delete_file_if_exists(context_file_path)
        except Exception as exc_file:
            logger.error(f"Error deleting PDF file {context_file_path}: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating question: {str(exc)}. The question was not created."
        )


@router.get("/questions", response_model=PaginatedQuestionResponse)
async def get_questions(
    page: int = Query(1, ge=1, description="Number of page (starting at 1)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Elements per page (maximum 100)"
    ),
    modality_id: Optional[str] = Query(None, description="Filter by modality"),
    submodality_id: Optional[str] = Query(None, description="Filter by submodality"),
    category_id: Optional[str] = Query(None, description="Filter by category"),
    context_type: Optional[str] = Query(None, description="Filter by context type"),
    status: Optional[str] = Query(
        None, description="Filter by status (use 'all' to show all)"
    ),
    search: Optional[str] = Query(None, description="Search in question text"),
    current_user=Depends(get_current_active_user),
):
    """Get paginated list of questions with optional filters"""
    async for session in get_async_session():
        # Load all relationships for flexible hierarchy
        query = select(Question).options(
            selectinload(Question.modality),
            selectinload(Question.submodality),
            selectinload(Question.category),
        )

        # Flexible hierarchy filtering
        if modality_id:
            query = query.where(Question.modality_id == modality_id)
        if submodality_id:
            query = query.where(Question.submodality_id == submodality_id)
        if category_id:
            query = query.where(Question.category_id == category_id)

        if context_type:
            query = query.where(Question.context_type == context_type)

        if status and status != "all":
            query = query.where(Question.status == status)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Question.question_text.ilike(search_term)) |
                (Question.model_response.ilike(search_term)) |
                (Question.context_text.ilike(search_term))
            )

        count_query = select(func.count(Question.id))
        # Apply same filters to count query
        if modality_id:
            count_query = count_query.where(Question.modality_id == modality_id)
        if submodality_id:
            count_query = count_query.where(Question.submodality_id == submodality_id)
        if category_id:
            count_query = count_query.where(Question.category_id == category_id)
        if context_type:
            count_query = count_query.where(Question.context_type == context_type)
        if status and status != "all":
            count_query = count_query.where(Question.status == status)
        if search:
            search_term = f"%{search}%"
            count_query = count_query.where(
                (Question.question_text.ilike(search_term)) |
                (Question.model_response.ilike(search_term)) |
                (Question.context_text.ilike(search_term))
            )

        total_count_result = await session.execute(count_query)
        total_items = total_count_result.scalar()

        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
        offset = (page - 1) * page_size

        query = query.order_by(Question.created_at.desc())
        query = query.offset(offset).limit(page_size)

        result = await session.execute(query)
        questions = result.scalars().all()

        response_questions = []
        for q in questions:
            response_questions.append(build_question_response(q))

        pagination_info = PaginationInfo(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )

        return PaginatedQuestionResponse(
            items=response_questions, pagination=pagination_info
        )


@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: str, current_user=Depends(get_current_active_user)):
    """Get a specific question by ID"""
    async for session in get_async_session():
        result = await session.execute(
            select(Question)
            .where(Question.id == question_id)
            .options(
                selectinload(Question.modality),
                selectinload(Question.submodality),
                selectinload(Question.category),
            )
        )
        question = result.scalar_one_or_none()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        return build_question_response(question)


@router.patch("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: str,
    question_text: Optional[str] = Form(None),
    context_type: Optional[str] = Form(None),
    context_text: Optional[str] = Form(None),
    context_file: Optional[UploadFile] = File(None),
    modality_id: Optional[str] = Form(None),
    submodality_id: Optional[str] = Form(None),
    category_id: Optional[str] = Form(None),
    model_response: Optional[str] = Form(None),
    current_user=Depends(get_current_active_user),
):
    """Update question using FormData (same as create)"""
    try:
        async for session in get_async_session():
            # Buscar la pregunta existente
            result = await session.execute(
                select(Question)
                .where(Question.id == question_id)
                .options(
                    selectinload(Question.modality),
                    selectinload(Question.submodality),
                    selectinload(Question.category),
                )
            )
            question = result.scalar_one_or_none()

            if not question:
                raise HTTPException(status_code=404, detail="Question not found")

            original_question_text = question.question_text
            original_context_text = question.context_text
            original_context_type = question.context_type
            original_context_file = question.context_file
            original_modality_id = str(question.modality_id or None)
            original_submodality_id = str(question.submodality_id or None)
            original_category_id = str(question.category_id or None)

            if question_text is not None:
                question.question_text = question_text

            if context_type is not None:
                if (
                    context_type == "text"
                    and not context_text
                    and not question.context_text
                ):
                    raise HTTPException(
                        status_code=400,
                        detail="context_text is required when context_type is 'text'",
                    )

                if (
                    context_type == "pdf"
                    and not context_file
                    and not question.context_file
                ):
                    raise HTTPException(
                        status_code=400,
                        detail="context_file is required when context_type is 'pdf'",
                    )

                question.context_type = context_type

            if context_text is not None:
                question.context_text = context_text

            if model_response and model_response.strip():
                question.model_response = model_response

            if context_file and context_type == "text":
                raise HTTPException(
                    status_code=400,
                    detail="Not possible to upload PDF file with context_type 'text'",
                )

            if context_type == "pdf" and not context_file and not question.context_file:
                raise HTTPException(
                    status_code=400,
                    detail="context_file is required when context_type is 'pdf'",
                )

            if context_file:
                if context_file.content_type != "application/pdf":
                    raise HTTPException(
                        status_code=400, detail="The file must be a PDF"
                    )

                context_file_path = await storage_service.upload_file(
                    context_file, "pdfs"
                )
                question.context_file = context_file_path

                if context_type is None:
                    question.context_type = "pdf"
                elif context_type != "pdf":
                    question.context_type = "pdf"

            # Handle hierarchy updates
            hierarchy_changed = False

            # Validate and update modality if provided
            if modality_id and modality_id.strip():
                modality = await session.get(Modality, modality_id)
                if not modality:
                    raise HTTPException(status_code=404, detail="Modality not found")
                if original_modality_id != modality_id:
                    question.modality_id = modality_id
                    # When modality changes, null submodality and category
                    question.submodality_id = None
                    question.category_id = None
                    hierarchy_changed = True
                    logger.info(f"Modality changed to {modality_id}, nulled submodality and category")

            # Validate and update submodality if provided
            if submodality_id and submodality_id.strip():
                submodality = await session.get(Submodality, submodality_id)
                if not submodality:
                    raise HTTPException(status_code=404, detail="Submodality not found")
                # Validate submodality belongs to current modality
                current_modality_id = question.modality_id
                if submodality.modality_id != current_modality_id:
                    raise HTTPException(
                        status_code=400,
                        detail="Submodality does not belong to the current modality",
                    )
                if original_submodality_id != submodality_id:
                    question.submodality_id = submodality_id
                    # When submodality changes, null category (only if modality didn't change)
                    if not hierarchy_changed:  # Only null category if modality didn't change
                        question.category_id = None
                        logger.info(f"Submodality changed to {submodality_id}, nulled category")
                    hierarchy_changed = True

            # Validate and update category if provided
            if category_id and category_id not in ("", "null") and category_id.strip():
                category = await session.get(Category, category_id)
                if not category:
                    raise HTTPException(status_code=404, detail="Category not found")
                # Validate category belongs to current modality
                if category.modality_id != question.modality_id:
                    raise HTTPException(
                        status_code=400,
                        detail="Category does not belong to the current modality",
                    )
                # Validate category belongs to current submodality (if both have submodality)
                current_submodality_id = question.submodality_id
                if current_submodality_id and category.submodality_id and category.submodality_id != current_submodality_id:
                    raise HTTPException(
                        status_code=400,
                        detail="Category does not belong to the current submodality",
                    )
                # If no submodality but category has submodality, auto-set submodality
                if not current_submodality_id and category.submodality_id:
                    question.submodality_id = category.submodality_id
                    logger.info(f"Auto-set submodality to {category.submodality_id} for category {category_id}")
                if original_category_id != category_id:
                    question.category_id = category_id
                    hierarchy_changed = True

            question.status = QuestionStatus.PENDING.value

            content_changed_for_regeneration = (
                (
                    question_text is not None
                    and question.question_text != original_question_text
                )
                or (
                    context_text is not None
                    and question.context_text != original_context_text
                )
                or (context_file is not None)
                or hierarchy_changed
            )

            original_model_response = question.model_response
            model_response_manually_edited = (
                model_response is not None and model_response != original_model_response
            )

            if content_changed_for_regeneration and not model_response_manually_edited:
                logger.info(
                    f"🤖 Regenerating response with Gemini for question: {question.question_text[:50]}..."
                )

                try:
                    new_model_response = await gemini_service.generate_response(
                        question_text=question.question_text,
                        context_text=question.context_text,
                        context_type=question.context_type,
                        context_file_path=question.context_file,
                        action="update",
                    )

                    logger.info(
                        f"New response generated: {len(new_model_response)} characters"
                    )

                    question.model_response = new_model_response

                except Exception as e:
                    logger.error(f"Error generating response with Gemini: {e}")
                    if not question.model_response:
                        question.model_response = f"Error generating response: {str(e)}"
            else:
                if model_response_manually_edited:
                    question.model_response = model_response

            # Regenerate embeddings if question_text changed or hierarchy changed
            if (
                question_text is not None
                and question.question_text != original_question_text
            ) or hierarchy_changed:
                logger.info(f"Regenerating embeddings for updated question...")
                try:
                    await embedding_service.recreate_embedding_for_question_text(
                        question_id=question_id,
                        question_text=question.question_text,
                        session=session,
                    )
                    logger.info(f"Embeddings regenerated for question {question_id}")
                except Exception as exc:
                    logger.error(
                        f"Error generating embedding for question {question_id}: {str(exc)}"
                    )
                    raise HTTPException(
                            status_code=500,
                            detail=f"Error generating embedding: {str(exc)}. The question was not created."
                        )

            await session.commit()

            # Reload question with all nested relationships to avoid lazy loading issues
            result = await session.execute(
                select(Question)
                .where(Question.id == question_id)
                .options(
                    selectinload(Question.modality),
                    selectinload(Question.submodality),
                    selectinload(Question.category)
                )
            )
            question = result.scalar_one()

            return build_question_response(question)

    except Exception as e:
        logger.error(f"Error in update_question: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/questions/{question_id}/recalculate", response_model=QuestionResponse)
async def recalculate_question(
    question_id: str, current_user=Depends(get_current_active_user)
):
    """Recalculate a question sending its current data to N8N"""
    try:
        async for session in get_async_session():
            result = await session.execute(
                select(Question)
                .where(Question.id == question_id)
                .options(
                    selectinload(Question.modality),
                    selectinload(Question.submodality),
                    selectinload(Question.category),
                )
            )
            question = result.scalar_one_or_none()

            if not question:
                raise HTTPException(status_code=404, detail="Question not found")

            logger.info(f"🤖 Recalculating response with Gemini for question {question_id}:")
            logger.info(f"  - question_text: {question.question_text}")
            logger.info(f"  - context_type: {question.context_type}")
            logger.info(f"  - category_id: {question.category_id}")

            new_model_response = await gemini_service.generate_response(
                question_text=question.question_text,
                context_text=question.context_text,
                context_type=question.context_type,
                context_file_path=question.context_file,
                action="recalculate",
            )
            logger.info(f"Response recalculated: {len(new_model_response)} characters")

            question.model_response = new_model_response
            question.status = QuestionStatus.PENDING.value
            await session.commit()
            await session.refresh(question)

            return build_question_response(question)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in recalculate_question: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/questions/{question_id}/file")
async def get_context_file(
    question_id: str, current_user=Depends(get_current_active_user)
):
    """Endpoint to download the context file of a question"""
    async for session in get_async_session():
        question = await session.get(Question, question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        if not question.context_file or question.context_type != "pdf":
            raise HTTPException(
                status_code=404, detail="No PDF file associated with this question"
            )

        if not storage_service.file_exists(question.context_file):
            raise HTTPException(status_code=404, detail="File not found in the server")

        try:
            file_stream = storage_service.get_file_stream(question.context_file)

            return StreamingResponse(
                file_stream,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": (
                        f"inline; filename=context_{question_id}.pdf"
                    )
                },
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error downloading file: {str(e)}"
            )


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: str, current_user=Depends(get_current_active_user)
):
    """Delete a question completely from database and associated files"""
    async for session in get_async_session():
        result = await session.execute(
            select(Question)
            .where(Question.id == question_id)
            .options(
                selectinload(Question.modality),
                selectinload(Question.submodality),
                selectinload(Question.category),
            )
        )
        question = result.scalar_one_or_none()

        if not question:
            raise HTTPException(status_code=404, detail="Pregunta no encontrada")

        # Delete associated PDF file from MinIO if exists
        if question.context_file and question.context_type == "pdf":
            try:
                await storage_service.delete_file(question.context_file)
                logger.info(f"PDF file deleted from MinIO: {question.context_file}")
            except Exception as e:
                logger.error(f"Error deleting PDF file {question.context_file}: {e}")
                # Continue with question deletion even if file deletion fails

        # Delete question from database
        await session.delete(question)
        await session.commit()

        logger.info(f"Question {question_id} completely deleted from database")

        return {"message": f"Question {question_id} successfully deleted"}


@router.patch("/questions/{question_id}/approval", response_model=QuestionResponse)
async def update_question_approval(
    question_id: str,
    approval_request: QuestionApprovalRequest,
    current_user=Depends(get_current_active_user),
):
    """Approve or disable a question"""
    async for session in get_async_session():
        result = await session.execute(
            select(Question)
            .where(Question.id == question_id)
            .options(
                selectinload(Question.modality),
                selectinload(Question.submodality),
                selectinload(Question.category),
            )
        )
        question = result.scalar_one_or_none()

        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        if approval_request.action == "approve":
            question.status = QuestionStatus.APPROVED.value
        elif approval_request.action == "disable":
            question.status = QuestionStatus.DISABLED.value

        await session.commit()
        await session.refresh(question)

        return build_question_response(question)


@router.post("/search-similarity", response_model=SimilaritySearchResponse)
async def search_similarity(
    request: SimilaritySearchRequest,
    session=Depends(get_async_session),
    # current_user=Depends(get_current_active_user),
):
    """
    Search for similar questions in the database using vector embeddings.

    This endpoint:
    1. Recieves a question text
    2. Generates a vector embedding using the all-MiniLM-L6-v2 model
    3. Searches in the chunk_embeddings table using cosine similarity with pgvector
    4. **IMPORTANT**: Only includes questions with status 'APPROVED'
    5. Returns the similar questions found or a message indicating that there are no similarities

    Security validations:
    - Only questions with status 'APPROVED' are included in the results
    - Questions with status 'PENDING' or 'DISABLED' are automatically excluded

    Args:
        request: Search data (text, similarity threshold, limit)
        session: Database session
        current_user: Authenticated user

    Returns:
        SimilaritySearchResponse: Result of the search with similar questions or message of no similarity
    """
    try:
        if not request.question_text.strip():
            raise HTTPException(
                status_code=400, detail="The question text cannot be empty"
            )

        logger.info(f"🔍 Searching for similarities for: '{request.question_text[:100]}...'")
        logger.info(
            f"Parameters: threshold={request.similarity_threshold}, limit={request.limit}"
        )

        similar_results = await embedding_service.search_by_text(
            query_text=request.question_text,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold,
            session=session,
        )

        logger.info(f"Found {len(similar_results)} similar results")

        if not similar_results:
            return SimilaritySearchResponse(
                query_text=request.question_text,
                found_similarities=False,
                message="No similar questions found with the specified similarity threshold.",
                similar_chunks=[],
                total_found=0,
            )

        similar_chunks = []
        for chunk_embedding, similarity_score, question_data in similar_results:
            similar_chunk = SimilarChunkResponse(
                chunk_id=chunk_embedding.id,
                question_id=chunk_embedding.question_id,
                chunk_text=chunk_embedding.chunk_text,
                similarity_score=round(similarity_score, 4),
                chunk_index=chunk_embedding.chunk_index,
                created_at=str(chunk_embedding.created_at),
                question_text=question_data.get("question_text"),
                model_response=question_data.get("model_response"),
                question_status=question_data.get("status"),
            )
            similar_chunks.append(similar_chunk)

        best_similarity = similar_chunks[0].similarity_score if similar_chunks else 0
        message = f"Found {len(similar_chunks)} similar questions. The best similarity is {best_similarity:.2%}."

        logger.info(f"Search completed successfully")

        return SimilaritySearchResponse(
            query_text=request.question_text,
            found_similarities=True,
            message=message,
            similar_chunks=similar_chunks,
            total_found=len(similar_chunks),
        )

    except Exception as e:
        logger.error(f"Error in similarity search: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error internal server during similarity search: {str(e)}",
        )
