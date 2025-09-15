# src/app/controllers/question.py
from fastapi import (
    APIRouter, HTTPException, UploadFile, File, Form, Query, Depends
)
from fastapi.responses import StreamingResponse
from src.app.db.session import get_async_session
from src.app.models import Question, Category
from src.app.schemas.question import (
    QuestionResponse, 
    QuestionApprovalRequest, 
    QuestionStatus,
    PaginatedQuestionResponse,
    PaginationInfo
)
from src.app.services.storage_service import storage_service
import httpx
import os
from typing import Optional
from sqlalchemy import select, func
import math
from sqlalchemy.orm import selectinload
from src.app.dependencies.auth import get_current_active_user


router = APIRouter()

N8N_WEBHOOK = os.getenv("N8N_WEBHOOK")


def simulate_n8n_response(question_text: str, context_type: str, action: str = "create") -> str:
    """Simular respuesta de N8N con model_response básico"""
    import random
    
    # Asegurar que siempre tenemos texto válido
    safe_question = question_text if question_text else "pregunta sin texto"
    safe_context = context_type if context_type else "text"
    safe_action = action if action else "procesamiento"
    
    responses = [
        f"Basándome en la pregunta '{safe_question[:50]}...', he analizado el contexto de tipo {safe_context} y generado esta respuesta completa. El procesamiento se realizó exitosamente utilizando algoritmos avanzados de procesamiento de lenguaje natural, considerando todos los elementos contextuales disponibles para proporcionar la información más precisa y relevante posible.",
        
        f"Después de procesar la consulta '{safe_question[:40]}...', el sistema ha evaluado el contenido {safe_context} y ha determinado que la respuesta óptima incluye múltiples aspectos relevantes. Esta respuesta ha sido generada considerando patrones de datos similares, contexto histórico y mejores prácticas en el dominio específico de la pregunta planteada.",
        
        f"El análisis de la pregunta '{safe_question[:45]}...' con contexto {safe_context} ha resultado en una respuesta comprehensiva que aborda los puntos clave identificados. El modelo ha procesado la información disponible, aplicado técnicas de inferencia contextual y generado una respuesta que busca ser tanto informativa como práctica para el usuario que realizó la consulta.",
        
        f"Procesamiento completado para '{safe_question[:35]}...'. El sistema ha analizado el contexto de tipo {safe_context} y ha generado esta respuesta detallada que incorpora conocimiento relevante del dominio. La acción de {safe_action} se ejecutó correctamente, resultando en una respuesta que combina precisión técnica con claridad comunicativa para el usuario final."
    ]
    
    return random.choice(responses)

@router.post("/questions", response_model=QuestionResponse)
async def create_question(
    question_text: str = Form(...),
    context_type: str = Form(...),
    context_text: Optional[str] = Form(None),
    context_file: Optional[UploadFile] = File(None),
    category_id: str = Form(...),
    current_user = Depends(get_current_active_user)
):
    """Crear pregunta usando FormData (texto o archivo)"""
    try:
        # Validaciones
        if context_type == "text" and not context_text:
            raise HTTPException(
                status_code=400,
                detail="context_text es requerido cuando context_type es 'text'"
            )

        if context_type == "pdf" and not context_file:
            raise HTTPException(
                status_code=400,
                detail="context_file es requerido cuando context_type es 'pdf'"
            )

        if context_file and context_file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail="El archivo debe ser un PDF"
            )
        
        # Validar consistencia entre context_type y context_file
        if context_file and context_type != "pdf":
            raise HTTPException(
                status_code=400,
                detail="Si se proporciona un archivo, context_type debe ser 'pdf'"
            )
        
        # Verificar si la categoría existe
        category_name = None
        async for session in get_async_session():
            category = await session.get(Category, category_id)
            if not category:
                raise HTTPException(status_code=404, detail="Categoría no encontrada")
            category_name = category.name
            break
        
        # Procesar archivo si se proporciona
        context_file_path = None
        if context_file:
            # Guardar archivo en MinIO/S3
            context_file_path = await storage_service.upload_file(
                context_file, "pdfs"
            )
        
        async for session in get_async_session():
            q = Question(
                question_text=question_text,
                context_text=context_text,
                context_type=context_type,
                context_file=context_file_path,
                category_id=category_id,
                status=QuestionStatus.PENDING.value
            )
            session.add(q)
            await session.commit()
            await session.refresh(q)
            question_id = str(q.id)

        # Procesar con N8N (simulado) y obtener model_response
        model_response = None
        if N8N_WEBHOOK:
            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    response = await client.post(N8N_WEBHOOK, json={
                        "question_id": question_id,
                        "question_text": question_text,
                        "context_text": context_text,
                        "context_type": context_type,
                        "context_file": context_file_path,
                        "category_id": category_id
                    })
                    # En un caso real, extraerías model_response de response.json()
                    # model_response = response.json().get("model_response")
                    model_response = simulate_n8n_response(question_text, context_type, "create")
                except Exception as e:
                    # log but we keep question created; n8n can be retried
                    print("n8n webhook failed:", e)
                    model_response = simulate_n8n_response(question_text, context_type, "create")
        else:
            # Simular respuesta cuando N8N no está configurado
            model_response = simulate_n8n_response(question_text, context_type, "create")
        
        # Actualizar la pregunta con la respuesta del modelo
        async for session in get_async_session():
            question = await session.get(Question, question_id)
            if question and model_response:
                question.model_response = model_response
                await session.commit()
            break

        return QuestionResponse(
            question_id=question_id,
            status=QuestionStatus.PENDING.value,
            question_text=question_text,
            context_type=context_type,
            context_text=context_text,
            context_file=context_file_path,
            category_id=category_id,
            category_name=category_name,
            model_response=model_response,
            created_at=str(q.created_at)
        )
    except Exception as e:
        print(f"Error in create_question: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.get("/questions", response_model=PaginatedQuestionResponse)
async def get_questions(
    page: int = Query(1, ge=1, description="Número de página (empezando en 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Elementos por página (máximo 100)"),
    category_id: Optional[str] = Query(
        None, description="Filtrar por categoría (usar 'all' para mostrar todas)"
    ),
    context_type: Optional[str] = Query(
        None, description="Filtrar por tipo de contexto"
    ),
    status: Optional[str] = Query(None, description="Filtrar por estado (usar 'all' para mostrar todos)"),
    search: Optional[str] = Query(
        None, description="Buscar texto en preguntas"
    ),
    current_user = Depends(get_current_active_user)
):
    """Obtener lista paginada de preguntas con filtros opcionales"""
    async for session in get_async_session():
        # Construir query base
        query = select(Question).options(
            selectinload(Question.category)
        )
        
        # Aplicar filtros
        if category_id and category_id != "all":
            query = query.where(Question.category_id == category_id)
        
        if context_type:
            query = query.where(Question.context_type == context_type)
        
        if status and status != "all":
            query = query.where(Question.status == status)
        
        if search:
            # Buscar en el texto de la pregunta y en el contexto de texto
            search_term = f"%{search}%"
            query = query.where(
                Question.question_text.ilike(search_term)
            )
        
        # Contar total de elementos (sin paginación)
        count_query = select(func.count(Question.id))
        if category_id and category_id != "all":
            count_query = count_query.where(Question.category_id == category_id)
        if context_type:
            count_query = count_query.where(Question.context_type == context_type)
        if status and status != "all":
            count_query = count_query.where(Question.status == status)
        if search:
            search_term = f"%{search}%"
            count_query = count_query.where(
                Question.question_text.ilike(search_term)
            )
        
        total_count_result = await session.execute(count_query)
        total_items = total_count_result.scalar()
        
        # Calcular paginación
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
        offset = (page - 1) * page_size
        
        # Aplicar paginación y ordenamiento
        query = query.order_by(Question.created_at.desc())
        query = query.offset(offset).limit(page_size)
        
        result = await session.execute(query)
        questions = result.scalars().all()
        
        # Construir respuesta
        response_questions = []
        for q in questions:
            response_questions.append(QuestionResponse(
                question_id=str(q.id),
                status=q.status,
                question_text=q.question_text,
                context_type=q.context_type,
                context_text=q.context_text,
                context_file=q.context_file,
                category_id=q.category_id,
                category_name=(
                    q.category.name if q.category else None
                ),
                model_response=q.model_response,
                created_at=str(q.created_at)
            ))
        
        # Crear información de paginación
        pagination_info = PaginationInfo(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )
        
        return PaginatedQuestionResponse(
            items=response_questions,
            pagination=pagination_info
        )

@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: str,
    current_user=Depends(get_current_active_user)
):
    """Obtener una pregunta específica por ID"""
    async for session in get_async_session():
        result = await session.execute(
            select(Question)
            .where(Question.id == question_id)
            .options(selectinload(Question.category))
        )
        question = result.scalar_one_or_none()
        if not question:
            raise HTTPException(status_code=404, detail="Pregunta no encontrada")
        
        return QuestionResponse(
            question_id=str(question.id),
            status=question.status,
            question_text=question.question_text,
            context_type=question.context_type,
            context_text=question.context_text,
            context_file=question.context_file,
            category_id=question.category_id,
            category_name=(
                question.category.name if question.category else None
            ),
            model_response=question.model_response,
            created_at=str(question.created_at)
        )


@router.patch("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: str,
    question_text: Optional[str] = Form(None),
    context_type: Optional[str] = Form(None),
    context_text: Optional[str] = Form(None),
    context_file: Optional[UploadFile] = File(None),
    category_id: Optional[str] = Form(None),
    model_response: Optional[str] = Form(None),
    current_user = Depends(get_current_active_user)
):
    """Actualizar pregunta usando FormData (igual que crear)"""
    try:
        async for session in get_async_session():
            # Buscar la pregunta existente
            result = await session.execute(
                select(Question)
                .where(Question.id == question_id)
                .options(selectinload(Question.category))
            )
            question = result.scalar_one_or_none()
            
            if not question:
                raise HTTPException(status_code=404, detail="Pregunta no encontrada")
            
            # Guardar valores originales para comparar
            original_context_type = question.context_type
            original_category_id = question.category_id
            
            # Actualizar campos si se proporcionaron
            if question_text is not None:
                question.question_text = question_text
            
            if context_type is not None:
                # Validaciones igual que en POST
                if context_type == "text" and not context_text and not question.context_text:
                    raise HTTPException(
                        status_code=400,
                        detail="context_text es requerido cuando context_type es 'text'"
                    )
                
                if context_type == "pdf" and not context_file and not question.context_file:
                    raise HTTPException(
                        status_code=400,
                        detail="context_file es requerido cuando context_type es 'pdf'"
                    )
                
                question.context_type = context_type
            
            if context_text is not None:
                question.context_text = context_text
            
            if model_response is not None:
                question.model_response = model_response
            
            # Validar consistencia entre context_type y context_file
            if context_file and context_type == "text":
                raise HTTPException(
                    status_code=400,
                    detail="No se puede subir archivo PDF con context_type 'text'"
                )
            
            if context_type == "pdf" and not context_file and not question.context_file:
                raise HTTPException(
                    status_code=400,
                    detail="context_file es requerido cuando context_type es 'pdf'"
                )
            
            # Procesar archivo si se proporciona
            if context_file:
                if context_file.content_type != "application/pdf":
                    raise HTTPException(
                        status_code=400,
                        detail="El archivo debe ser un PDF"
                    )
                
                # Guardar nuevo archivo en MinIO/S3
                context_file_path = await storage_service.upload_file(
                    context_file, "pdfs"
                )
                question.context_file = context_file_path
                
                # Si se sube un archivo, el tipo debe ser PDF
                if context_type is None:
                    question.context_type = "pdf"
                elif context_type != "pdf":
                    # Forzar PDF si se sube archivo
                    question.context_type = "pdf"
            
            # Verificar y actualizar categoría
            if category_id is not None:
                category = await session.get(Category, category_id)
                if not category:
                    raise HTTPException(status_code=404, detail="Categoría no encontrada")
                question.category_id = category_id
            
            # Al actualizar una pregunta, vuelve a estado PENDING
            question.status = QuestionStatus.PENDING.value
            
            await session.commit()
            await session.refresh(question)
            
            # Verificar si necesitamos disparar el webhook de N8N
            should_trigger_n8n = (
                (context_type is not None and context_type != original_context_type) or
                (category_id is not None and category_id != original_category_id)
            )
            
            # Disparar webhook de N8N si es necesario y generar nueva respuesta
            if should_trigger_n8n:
                new_model_response = None
                if N8N_WEBHOOK:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        try:
                            response = await client.post(N8N_WEBHOOK, json={
                                "question_id": question_id,
                                "question_text": question.question_text,
                                "context_text": question.context_text,
                                "context_type": question.context_type,
                                "context_file": question.context_file,
                                "category_id": question.category_id,
                                "action": "update"
                            })
                            # En un caso real, extraerías model_response de response.json()
                            new_model_response = simulate_n8n_response(question.question_text, question.context_type, "update")
                        except Exception as e:
                            # Log pero continuamos, N8N puede reintentarse
                            print("n8n webhook failed on update:", e)
                            new_model_response = simulate_n8n_response(question.question_text, question.context_type, "update")
                else:
                    # Simular respuesta cuando N8N no está configurado
                    new_model_response = simulate_n8n_response(question.question_text, question.context_type, "update")
                
                # Solo actualizar model_response automáticamente si no se editó manualmente
                if model_response is None and new_model_response:
                    question.model_response = new_model_response
            
            return QuestionResponse(
                question_id=str(question.id),
                status=question.status,
                question_text=question.question_text,
                context_type=question.context_type,
                context_text=question.context_text,
                context_file=question.context_file,
                category_id=question.category_id,
                category_name=(
                    question.category.name if question.category else None
                ),
                created_at=str(question.created_at)
            )
            
    except Exception as e:
        print(f"Error in update_question: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/questions/{question_id}/recalculate", response_model=QuestionResponse)
async def recalculate_question(
    question_id: str,
    current_user = Depends(get_current_active_user)
):
    """Recalcular una pregunta enviando sus datos actuales a N8N"""
    try:
        async for session in get_async_session():
            # Buscar la pregunta existente
            result = await session.execute(
                select(Question)
                .where(Question.id == question_id)
                .options(selectinload(Question.category))
            )
            question = result.scalar_one_or_none()
            
            if not question:
                raise HTTPException(status_code=404, detail="Pregunta no encontrada")
            
            # Disparar webhook de N8N con los datos actuales y obtener nueva respuesta
            new_model_response = None
            if N8N_WEBHOOK:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    try:
                        response = await client.post(N8N_WEBHOOK, json={
                            "question_id": question_id,
                            "question_text": question.question_text,
                            "context_text": question.context_text,
                            "context_type": question.context_type,
                            "context_file": question.context_file,
                            "category_id": question.category_id,
                            "action": "recalculate"
                        })
                        # En un caso real, extraerías model_response de response.json()
                        new_model_response = simulate_n8n_response(question.question_text, question.context_type, "recalculate")
                    except Exception as e:
                        # Log pero continuamos
                        print("n8n webhook failed on recalculate:", e)
                        new_model_response = simulate_n8n_response(question.question_text, question.context_type, "recalculate")
            else:
                # Simular el procesamiento cuando N8N no está configurado
                print(f"Simulando recálculo para pregunta {question_id}:")
                print(f"  - question_text: {question.question_text}")
                print(f"  - context_type: {question.context_type}")
                print(f"  - category_id: {question.category_id}")
                print(f"  - action: recalculate")
                new_model_response = simulate_n8n_response(question.question_text, question.context_type, "recalculate")
            
            # Actualizar la pregunta con la nueva respuesta del modelo
            # Asegurar que siempre tengamos una respuesta
            if not new_model_response:
                new_model_response = simulate_n8n_response(question.question_text, question.context_type, "recalculate")
            
            question.model_response = new_model_response
            # Al recalcular, vuelve a estado PENDING para revisión
            question.status = QuestionStatus.PENDING.value
            await session.commit()
            await session.refresh(question)
            
            return QuestionResponse(
                question_id=str(question.id),
                status=question.status,
                question_text=question.question_text,
                context_type=question.context_type,
                context_text=question.context_text,
                context_file=question.context_file,
                category_id=question.category_id,
                category_name=(
                    question.category.name if question.category else None
                ),
                model_response=question.model_response,
                created_at=str(question.created_at)
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in recalculate_question: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/questions/{question_id}/file")
async def get_context_file(
    question_id: str,
    current_user=Depends(get_current_active_user)
):
    """Endpoint para descargar el archivo de contexto de una pregunta"""
    async for session in get_async_session():
        question = await session.get(Question, question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Pregunta no encontrada")
        
        if not question.context_file or question.context_type != "pdf":
            raise HTTPException(
                status_code=404,
                detail="No hay archivo PDF asociado a esta pregunta"
            )
        
        # Verificar si el archivo existe en MinIO
        if not storage_service.file_exists(question.context_file):
            raise HTTPException(
                status_code=404,
                detail="Archivo no encontrado en el servidor"
            )
        
        # Obtener el stream del archivo desde MinIO
        try:
            file_stream = storage_service.get_file_stream(
                question.context_file
            )

            return StreamingResponse(
                file_stream,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": (
                        f"inline; filename=context_{question_id}.pdf"
                    )
                }
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al descargar archivo: {str(e)}"
            )

@router.delete("/questions/{question_id}", response_model=QuestionResponse)
async def delete_question(
    question_id: str,
    current_user=Depends(get_current_active_user)
):
    """Eliminar una pregunta (cambiar estado a DISABLED)"""
    async for session in get_async_session():
        # Buscar la pregunta
        result = await session.execute(
            select(Question)
            .where(Question.id == question_id)
            .options(selectinload(Question.category))
        )
        question = result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(status_code=404, detail="Pregunta no encontrada")
        
        # Verificar que la pregunta no esté ya deshabilitada
        if question.status == QuestionStatus.DISABLED.value:
            raise HTTPException(
                status_code=400, 
                detail="La pregunta ya está deshabilitada"
            )
        
        # Cambiar estado a DISABLED
        question.status = QuestionStatus.DISABLED.value
        
        await session.commit()
        await session.refresh(question)
        
        return QuestionResponse(
            question_id=str(question.id),
            status=question.status,
            question_text=question.question_text,
            context_type=question.context_type,
            context_text=question.context_text,
            context_file=question.context_file,
            category_id=question.category_id,
            category_name=(
                question.category.name if question.category else None
            ),
            model_response=question.model_response,
            created_at=str(question.created_at)
        )


@router.patch("/questions/{question_id}/approval", response_model=QuestionResponse)
async def update_question_approval(
    question_id: str,
    approval_request: QuestionApprovalRequest,
    current_user=Depends(get_current_active_user)
):
    """Aprobar o deshabilitar una pregunta"""
    async for session in get_async_session():
        # Buscar la pregunta
        result = await session.execute(
            select(Question)
            .where(Question.id == question_id)
            .options(selectinload(Question.category))
        )
        question = result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(status_code=404, detail="Pregunta no encontrada")
        
        # Actualizar el estado según la acción
        if approval_request.action == "approve":
            question.status = QuestionStatus.APPROVED.value
        elif approval_request.action == "disable":
            question.status = QuestionStatus.DISABLED.value
        
        await session.commit()
        await session.refresh(question)
        
        return QuestionResponse(
            question_id=str(question.id),
            status=question.status,
            question_text=question.question_text,
            context_type=question.context_type,
            context_text=question.context_text,
            context_file=question.context_file,
            category_id=question.category_id,
            category_name=(
                question.category.name if question.category else None
            ),
            model_response=question.model_response,
            created_at=str(question.created_at)
        )
