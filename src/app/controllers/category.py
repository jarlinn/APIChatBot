"""
Controllers for Categories
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.app.db.session import get_async_session
from src.app.models import Submodality, Category
from src.app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from src.app.dependencies.auth import get_current_active_user
from src.app.utils.string_utils import generate_slug

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=List[CategoryResponse])
async def get_categories(
    skip: int = Query(0, ge=0, description="Number of elements to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of elements to return"
    ),
    submodality_id: Optional[str] = Query(None, description="Filter by submodality"),
    current_user=Depends(get_current_active_user),
):
    """Get list of categories"""
    async for session in get_async_session():
        query = select(Category).options(
            selectinload(Category.submodality).selectinload(Submodality.modality),
            selectinload(Category.questions),
        )

        if submodality_id:
            query = query.where(Category.submodality_id == submodality_id)

        query = query.offset(skip).limit(limit).order_by(Category.name)

        result = await session.execute(query)
        categories = result.scalars().all()

        return [
            CategoryResponse(
                id=cat.id,
                name=cat.name,
                slug=cat.slug,
                description=cat.description,
                submodality_id=cat.submodality_id,
                created_at=cat.created_at,
                updated_at=cat.updated_at,
                submodality_name=cat.submodality.name if cat.submodality else None,
                modality_name=(
                    cat.submodality.modality.name
                    if cat.submodality and cat.submodality.modality
                    else None
                ),
                full_name=cat.full_name,
                full_path=cat.full_path,
                total_questions=cat.total_questions,
            )
            for cat in categories
        ]


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: str, current_user=Depends(get_current_active_user)):
    """Get a specific category"""
    async for session in get_async_session():
        result = await session.execute(
            select(Category)
            .where(Category.id == category_id)
            .options(
                selectinload(Category.submodality).selectinload(Submodality.modality),
                selectinload(Category.questions),
            )
        )
        category = result.scalar_one_or_none()

        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        return CategoryResponse(
            id=category.id,
            name=category.name,
            slug=category.slug,
            description=category.description,
            submodality_id=category.submodality_id,
            created_at=category.created_at,
            updated_at=category.updated_at,
            submodality_name=(
                category.submodality.name if category.submodality else None
            ),
            modality_name=(
                category.submodality.modality.name
                if category.submodality and category.submodality.modality
                else None
            ),
            full_name=category.full_name,
            full_path=category.full_path,
            total_questions=category.total_questions,
        )


@router.post("/", response_model=CategoryResponse)
async def create_category(
    category_data: CategoryCreate, current_user=Depends(get_current_active_user)
):
    """Create a new category"""
    async for session in get_async_session():
        submodality = await session.get(Submodality, category_data.submodality_id)
        if not submodality:
            raise HTTPException(status_code=404, detail="Submodality not found")

        # Check if category with same name already exists for this submodality
        existing_name = await session.execute(
            select(Category).where(
                Category.submodality_id == category_data.submodality_id,
                Category.name == category_data.name,
            )
        )
        if existing_name.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail="Ya existe una categoría con ese nombre en esta submodalidad"
            )

        base_slug = generate_slug(category_data.name)
        slug = base_slug

        counter = 1
        while True:
            existing = await session.execute(
                select(Category).where(
                    Category.submodality_id == category_data.submodality_id,
                    Category.slug == slug,
                )
            )
            if not existing.scalar_one_or_none():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1

        category = Category(
            name=category_data.name,
            slug=slug,
            description=category_data.description,
            submodality_id=category_data.submodality_id,
        )

        session.add(category)
        await session.commit()
        await session.refresh(category)
        await session.refresh(category, ["submodality"])
        await session.refresh(category.submodality, ["modality"])

        return CategoryResponse(
            id=category.id,
            name=category.name,
            slug=category.slug,
            description=category.description,
            submodality_id=category.submodality_id,
            created_at=category.created_at,
            updated_at=category.updated_at,
            submodality_name=submodality.name,
            modality_name=submodality.modality.name if submodality.modality else None,
            full_name=category.full_name,
            full_path=category.full_path,
            total_questions=0,
        )


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    category_data: CategoryUpdate,
    current_user=Depends(get_current_active_user),
):
    """Update a category"""
    async for session in get_async_session():
        result = await session.execute(
            select(Category)
            .where(Category.id == category_id)
            .options(
                selectinload(Category.submodality).selectinload(Submodality.modality),
                selectinload(Category.questions),
            )
        )
        category = result.scalar_one_or_none()

        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        if (
            category_data.submodality_id
            and category_data.submodality_id != category.submodality_id
        ):
            submodality = await session.get(Submodality, category_data.submodality_id)
            if not submodality:
                raise HTTPException(status_code=404, detail="Submodality not found")

        if category_data.name is not None:
            # Check if another category with same name exists for this submodality
            submodality_id_to_check = (
                category_data.submodality_id or category.submodality_id
            )
            existing_name = await session.execute(
                select(Category).where(
                    Category.submodality_id == submodality_id_to_check,
                    Category.name == category_data.name,
                    Category.id != category_id,
                )
            )
            if existing_name.scalar_one_or_none():
                raise HTTPException(
                    status_code=409,
                    detail="Ya existe otra categoría con ese nombre en esta submodalidad"
                )

            category.name = category_data.name
            base_slug = generate_slug(category_data.name)
            slug = base_slug

            counter = 1
            while True:
                existing = await session.execute(
                    select(Category).where(
                        Category.submodality_id == submodality_id_to_check,
                        Category.slug == slug,
                        Category.id != category_id,
                    )
                )
                if not existing.scalar_one_or_none():
                    break
                slug = f"{base_slug}-{counter}"
                counter += 1

            category.slug = slug

        if category_data.description is not None:
            category.description = category_data.description
        if category_data.submodality_id is not None:
            category.submodality_id = category_data.submodality_id

        await session.commit()
        await session.refresh(category)
        await session.refresh(category, ["submodality"])
        await session.refresh(category.submodality, ["modality"])

        return CategoryResponse(
            id=category.id,
            name=category.name,
            slug=category.slug,
            description=category.description,
            submodality_id=category.submodality_id,
            created_at=category.created_at,
            updated_at=category.updated_at,
            submodality_name=(
                category.submodality.name if category.submodality else None
            ),
            modality_name=(
                category.submodality.modality.name
                if category.submodality and category.submodality.modality
                else None
            ),
            full_name=category.full_name,
            full_path=category.full_path,
            total_questions=category.total_questions,
        )


@router.delete("/{category_id}")
async def delete_category(
    category_id: str, current_user=Depends(get_current_active_user)
):
    """Delete a category (only if it has no questions)"""
    async for session in get_async_session():
        result = await session.execute(
            select(Category)
            .where(Category.id == category_id)
            .options(selectinload(Category.questions))
        )
        category = result.scalar_one_or_none()

        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        if category.questions:
            raise HTTPException(
                status_code=400, detail="Cannot delete a category that has questions"
            )

        await session.delete(category)
        await session.commit()

        return {"message": "Category deleted successfully"}
