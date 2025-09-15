from venv import logger
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from src.app.db.session import get_async_session
from src.app.models.category import Category
from src.app.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryTree
)
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from src.app.dependencies.auth import get_current_active_user
from src.app.utils.string_utils import generate_slug

router = APIRouter()

@router.post("/categories", response_model=CategoryResponse)
async def create_category(
    payload: CategoryCreate,
    current_user = Depends(get_current_active_user)
):
    """Crear una nueva categoría"""
    try:
        async for session in get_async_session():
            # Generar slug si no se proporciona
            slug = payload.slug if payload.slug else generate_slug(payload.name)
            
            # Verificar si el slug ya existe
            existing = await session.execute(
                select(Category).where(Category.slug == slug)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="El slug ya existe")
            
            # Calcular el nivel basado en el padre
            level = 0
            if payload.parent_id:
                parent = await session.get(Category, payload.parent_id)
                if not parent:
                    raise HTTPException(status_code=404, detail="Categoría padre no encontrada")
                level = parent.level + 1
            
            # Crear la categoría con los campos base
            category = Category(
                name=payload.name,
                slug=slug,  # Usar el slug generado
                description=payload.description,
                parent_id=payload.parent_id,
                level=level,
                is_active=True
            )
            
            session.add(category)
            await session.commit()
            await session.refresh(category)
            
            # Obtener conteos usando subconsultas SQL
            children_count_query = await session.execute(
                select(func.count()).select_from(Category).where(Category.parent_id == str(category.id))
            )
            children_count = children_count_query.scalar() or 0
            
            questions_count = 0  # Una categoría nueva no tiene preguntas
            
            # Obtener información del padre y construir la jerarquía completa
            full_path = category.slug
            display_name = category.name
            current = category
            
            while getattr(current, 'parent_id', None) is not None:
                parent = await session.get(Category, current.parent_id)
                if parent:
                    full_path = f"{parent.slug}/{full_path}"
                    display_name = f"{parent.name} > {display_name}"
                    current = parent
                else:
                    break

            # Retornar respuesta con valores convertidos de forma segura
            return CategoryResponse(
                id=str(category.id),
                name=str(category.name),
                slug=str(category.slug),
                description=str(category.description) if category.description is not None else None,
                parent_id=str(getattr(category, 'parent_id', None)) if getattr(category, 'parent_id', None) is not None else None,
                level=int(getattr(category, 'level', 0)),
                is_active=bool(category.is_active),
                full_path=str(full_path),
                display_name=str(display_name),
                children_count=children_count,
                questions_count=questions_count
            )
    except Exception as e:
        print(f"Error creando categoría: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(
    parent_id: Optional[str] = Query(None, description="ID de la categoría padre para filtrar"),
    level: Optional[int] = Query(None, description="Nivel específico para filtrar"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    current_user = Depends(get_current_active_user),
    session = Depends(get_async_session)
):
    """Obtener lista de categorías con filtros opcionales"""
    try:
        # Primero obtener todas las categorías para construir el mapeo de padres
        all_categories_query = select(Category).options(
            selectinload(Category.questions)
        )
        all_result = await session.execute(all_categories_query)
        all_categories = all_result.scalars().all()
        
        # Crear mapeo de categorías por ID para búsqueda rápida
        categories_by_id = {str(cat.id): cat for cat in all_categories}
        
        # Ahora aplicar filtros
        query = select(Category).options(
            selectinload(Category.questions)
        )
        
        if parent_id is not None:
            query = query.where(Category.parent_id == parent_id)
        
        if level is not None:
            query = query.where(Category.level == level)
        
        if is_active is not None:
            query = query.where(Category.is_active == is_active)
        
        # Ordenar por nivel y nombre
        query = query.order_by(Category.level, Category.name)
        
        result = await session.execute(query)
        categories = result.scalars().all()
        
        # Convertir categorías a response con conteos
        response_categories = []
        for cat in categories:
            try:
                # Contar hijos
                children_count_query = await session.execute(
                    select(func.count(Category.id)).where(Category.parent_id == str(cat.id))
                )
                children_count = children_count_query.scalar()
                
                # Contar preguntas
                questions_count = len(cat.questions) if hasattr(cat, 'questions') and cat.questions else 0
                
                # Construir full_path y display_name con la jerarquía completa usando el mapeo
                full_path = cat.slug
                display_name = cat.name
                current = cat
                
                while current.parent_id is not None:
                    parent = categories_by_id.get(str(current.parent_id))
                    if parent:
                        full_path = f"{parent.slug}/{full_path}"
                        display_name = f"{parent.name} > {display_name}"
                        current = parent
                    else:
                        break

                response_categories.append(CategoryResponse(
                    id=str(cat.id),
                    name=str(cat.name),
                    slug=str(cat.slug),
                    description=str(cat.description) if cat.description is not None else None,
                    parent_id=str(cat.parent_id) if cat.parent_id is not None else None,
                    level=int(cat.level),
                    is_active=bool(cat.is_active),
                    full_path=str(full_path),
                    display_name=str(display_name),
                    children_count=children_count,
                    questions_count=questions_count
                ))
            except Exception as e:
                print(f"Error processing category {cat.id}: {e}")
                # Agregar categoría con valores por defecto si hay error
                response_categories.append(CategoryResponse(
                    id=str(cat.id),
                    name=str(cat.name),
                    slug=str(cat.slug),
                    description=None,
                    parent_id=None,
                    level=0,
                    is_active=True,
                    full_path=str(cat.slug),  # Fallback
                    display_name=str(cat.name),  # Fallback
                    children_count=0,
                    questions_count=0
                ))
        
        return response_categories
    except Exception as e:
        print(f"Error in get_categories: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


@router.get("/categories/tree", response_model=List[CategoryTree])
async def get_categories_tree(
    current_user = Depends(get_current_active_user),
    session = Depends(get_async_session)
):
    """Obtener categorías en formato de árbol jerárquico con subcategorías anidadas"""
    try:
        # Obtener todas las categorías activas con sus relaciones cargadas
        query = select(Category).where(Category.is_active.is_(True)).options(
            selectinload(Category.questions),
            selectinload(Category.parent)
        ).order_by(Category.level, Category.name)
        result = await session.execute(query)
        all_categories = result.scalars().all()
        
        # Crear un diccionario para mapear categorías por ID para búsqueda rápida
        categories_by_id = {str(cat.id): cat for cat in all_categories}
        
        # Crear un diccionario para mapear categorías por ID
        categories_dict = {}
        for cat in all_categories:
            # Contar preguntas para cada categoría
            questions_count = len(cat.questions) if hasattr(cat, 'questions') and cat.questions else 0
            
            # Construir full_path usando el diccionario local
            full_path = cat.slug
            current = cat
            while current.parent_id is not None:
                parent = categories_by_id.get(str(current.parent_id))
                if parent:
                    full_path = f"{parent.slug}/{full_path}"
                    current = parent
                else:
                    break
            
            categories_dict[str(cat.id)] = CategoryTree(
                id=str(cat.id),
                name=str(cat.name),
                slug=str(cat.slug),
                description=str(cat.description) if cat.description else None,
                level=int(cat.level),
                is_active=bool(cat.is_active),
                full_path=str(full_path),
                children=[],
                questions_count=questions_count
            )
        
        # Construir el árbol jerárquico
        root_categories = []
        for cat in all_categories:
            cat_tree = categories_dict[str(cat.id)]
            
            if cat.parent_id is None:
                # Es una categoría raíz
                root_categories.append(cat_tree)
            else:
                # Es una subcategoría, agregarla a su padre
                parent_id = str(cat.parent_id)
                if parent_id in categories_dict:
                    categories_dict[parent_id].children.append(cat_tree)
        
        return root_categories
        
    except Exception as e:
        print(f"Error in get_categories_tree: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: str, current_user = Depends(get_current_active_user)):
    """Obtener una categoría específica por ID"""
    async for session in get_async_session():
        query = select(Category).where(Category.id == category_id).options(
            selectinload(Category.questions),
            selectinload(Category.children)
        )
        result = await session.execute(query)
        category = result.scalar_one_or_none()
        
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        
        # Contar hijos
        children_count_query = await session.execute(
            select(func.count(Category.id)).where(Category.parent_id == category_id)
        )
        children_count = children_count_query.scalar() or 0
        
        # Contar preguntas
        questions_count = len(category.questions) if hasattr(category, 'questions') else 0
        
        # Construir full_path y display_name con la jerarquía completa
        full_path = category.slug
        display_name = category.name
        current = category
        
        while getattr(current, 'parent_id', None) is not None:
            parent = await session.get(Category, current.parent_id)
            if parent:
                full_path = f"{parent.slug}/{full_path}"
                display_name = f"{parent.name} > {display_name}"
                current = parent
            else:
                break

        return CategoryResponse(
            id=str(category.id),
            name=str(category.name),
            slug=str(category.slug),
            description=str(category.description) if category.description is not None else None,
            parent_id=str(category.parent_id) if category.parent_id is not None else None,
            level=int(getattr(category, 'level', 0)),
            is_active=bool(category.is_active),
            full_path=str(full_path),
            display_name=str(display_name),
            children_count=children_count,
            questions_count=questions_count
        )

@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str, 
    payload: CategoryUpdate,
    current_user = Depends(get_current_active_user)
):
    """Actualizar una categoría existente"""
    try:
        async for session in get_async_session():
            # Obtener la categoría y sus relaciones
            category = await session.execute(
                select(Category)
                .where(Category.id == category_id)
                .options(selectinload(Category.questions))
            )
            category = category.scalar_one_or_none()
            if not category:
                raise HTTPException(status_code=404, detail="Categoría no encontrada")
            
            # Verificar si el slug ya existe (si se está cambiando)
            if payload.slug and payload.slug != category.slug:
                existing = await session.execute(
                    select(Category).where(Category.slug == payload.slug)
                )
                if existing.scalar_one_or_none():
                    raise HTTPException(status_code=400, detail="El slug ya existe")
            
            # Actualizar campos básicos
            if payload.name is not None:
                category.name = payload.name
            if payload.slug is not None:
                category.slug = payload.slug
            if payload.description is not None:
                category.description = payload.description
            if payload.is_active is not None:
                category.is_active = payload.is_active
            
            # Actualizar parent_id y recalcular nivel
            if payload.parent_id is not None:
                logger.info(f"Updating parent_id to {payload.parent_id} for category {category_id}")
                if payload.parent_id:
                    # Verificar que el nuevo padre existe
                    parent = await session.get(Category, payload.parent_id)
                    if not parent:
                        raise HTTPException(status_code=404, detail="Categoría padre no encontrada")
                    # Actualizar parent_id y nivel
                    category.parent_id = payload.parent_id
                    category.level = parent.level + 1 if parent.level is not None else 1
                else:
                    # Si se elimina el padre (parent_id = null)
                    category.parent_id = None
                    category.level = 0
            
            # Guardar cambios
            await session.commit()
            await session.refresh(category)
            
            # Obtener conteos usando subconsultas SQL
            children_count_query = await session.execute(
                select(func.count()).select_from(Category).where(Category.parent_id == category_id)
            )
            children_count = children_count_query.scalar() or 0
            
            questions_count_query = await session.execute(
                select(func.count()).where(Category.parent_id == category_id)
            )
            questions_count = questions_count_query.scalar() or 0

            # Retornar respuesta con valores convertidos de forma segura
            return CategoryResponse(
                id=str(category.id),
                name=str(category.name),
                slug=str(category.slug),
                description=str(category.description) if category.description is not None else None,
                parent_id=str(category.parent_id) if category.parent_id is not None else None,
                level=category.level,  # Ya es un entero
                is_active=bool(category.is_active),
                full_path=str(category.full_path or ""),  # Manejar caso null
                display_name=str(category.display_name or ""),  # Manejar caso null
                children_count=children_count,
                questions_count=questions_count
            )
    except Exception as e:
        logger.warning(f"Error actualizando categoría: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    current_user = Depends(get_current_active_user)
):
    """Eliminar una categoría (solo si no tiene hijos ni preguntas)"""
    async for session in get_async_session():
        category = await session.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        
        # Verificar si tiene hijos
        children_count = await session.execute(
            select(func.count(Category.id)).where(Category.parent_id == category_id)
        )
        if children_count.scalar() > 0:
            raise HTTPException(status_code=400, detail="No se puede eliminar una categoría que tiene subcategorías")
        
        # Verificar si tiene preguntas
        questions_count = await session.execute(
            select(func.count(category.questions))
        )
        if questions_count.scalar() > 0:
            raise HTTPException(status_code=400, detail="No se puede eliminar una categoría que tiene preguntas asociadas")
        
        await session.delete(category)
        await session.commit()
        
        return {"message": "Categoría eliminada exitosamente"}
