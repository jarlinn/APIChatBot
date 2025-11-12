"""
Controllers for Categories
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from src.app.db.session import get_async_session
from src.app.models import Modality, Submodality, Category
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
    modality_id: Optional[str] = Query(None, description="Filter by modality"),
    submodality_id: Optional[str] = Query(None, description="Filter by submodality"),
    current_user=Depends(get_current_active_user),
):
    """Get list of categories"""
    async for session in get_async_session():
        query = select(Category).options(
            selectinload(Category.direct_modality),
            selectinload(Category.submodality).selectinload(Submodality.modality),
            selectinload(Category.questions),
        )

        # Apply filters
        if modality_id:
            query = query.where(Category.modality_id == modality_id)
        if submodality_id:
            if submodality_id == "null":
                query = query.where(Category.submodality_id.is_(None))
            else:
                query = query.where(Category.submodality_id == submodality_id)

        query = query.offset(skip).limit(limit).order_by(Category.modality_id, Category.name)

        result = await session.execute(query)
        categories = result.scalars().all()

        return [
            CategoryResponse.from_orm(cat)
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
            modality_id=category.modality_id,
            submodality_id=category.submodality_id,
            created_at=category.created_at,
            updated_at=category.updated_at,
            submodality_name=category.submodality_name,
            modality_name=category.modality_name,
            full_name=category.full_name,
            full_path=category.full_path,
            total_questions=len(category.questions),
        )


@router.post("/", response_model=CategoryResponse)
async def create_category(
    category_data: CategoryCreate, current_user=Depends(get_current_active_user)
):
    """Create a new category"""
    async for session in get_async_session():
        # Prioritize submodality_id if provided, else modality_id
        if category_data.submodality_id:
            parent_id = category_data.submodality_id
            parent_type = "submodality"
            parent_model = Submodality
            category_submodality_id = category_data.submodality_id
        else:
            parent_id = category_data.modality_id
            parent_type = "modality"
            parent_model = Modality
            category_submodality_id = None

        parent = await session.get(parent_model, parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail=f"{parent_type.capitalize()} not found")

        # Set modality_id
        if parent_type == "submodality":
            category_modality_id = parent.modality_id
        else:
            category_modality_id = category_data.modality_id

        # Check if category with same name already exists for this parent
        parent_field = Category.submodality_id if parent_type == "submodality" else Category.modality_id
        existing_name = await session.execute(
            select(Category).where(
                parent_field == parent_id,
                Category.name == category_data.name,
            )
        )
        if existing_name.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe una categoría con ese nombre en esta {parent_type}"
            )

        base_slug = generate_slug(category_data.name)
        slug = base_slug

        counter = 1
        while True:
            existing = await session.execute(
                select(Category).where(
                    parent_field == parent_id,
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
            modality_id=category_modality_id,
            submodality_id=category_submodality_id,
        )

        session.add(category)
        await session.commit()
        await session.refresh(category)
        if category.submodality:
            await session.refresh(category, ["submodality"])
            await session.refresh(category.submodality, ["modality"])
        elif category.direct_modality:
            await session.refresh(category, ["direct_modality"])

        return CategoryResponse(
            id=category.id,
            name=category.name,
            slug=category.slug,
            description=category.description,
            modality_id=category.modality_id,
            submodality_id=category.submodality_id,
            created_at=category.created_at,
            updated_at=category.updated_at,
            submodality_name=category.submodality_name,
            modality_name=category.modality_name,
            full_name=category.full_name,
            full_path=category.full_path,
            total_questions=0,  # New category has no questions
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
                selectinload(Category.direct_modality),
                selectinload(Category.submodality).selectinload(Submodality.modality),
                selectinload(Category.questions),
            )
        )
        category = result.scalar_one_or_none()

        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        # Check parent changes
        if 'modality_id' in category_data.model_fields_set and category_data.modality_id != category.modality_id:
            if category_data.modality_id:
                modality = await session.get(Modality, category_data.modality_id)
                if not modality:
                    raise HTTPException(status_code=404, detail="Modality not found")
        if 'submodality_id' in category_data.model_fields_set and category_data.submodality_id != category.submodality_id:
            if category_data.submodality_id and category_data.submodality_id != "null":
                submodality = await session.get(Submodality, category_data.submodality_id)
                if not submodality:
                    raise HTTPException(status_code=404, detail="Submodality not found")

        # Update fields
        if 'modality_id' in category_data.model_fields_set:
            category.modality_id = category_data.modality_id
        if 'submodality_id' in category_data.model_fields_set:
            if category_data.submodality_id == "null":
                category.submodality_id = None
            else:
                category.submodality_id = category_data.submodality_id

        if category_data.name is not None:
            # Determine parent for uniqueness check
            parent_id = category.submodality_id or category.modality_id
            parent_type = "submodality" if category.submodality_id else "modality"
            parent_field = Category.submodality_id if parent_type == "submodality" else Category.modality_id
            existing_name = await session.execute(
                select(Category).where(
                    parent_field == parent_id,
                    Category.name == category_data.name,
                    Category.id != category_id,
                )
            )
            if existing_name.scalar_one_or_none():
                raise HTTPException(
                    status_code=409,
                    detail=f"Ya existe otra categoría con ese nombre en esta {parent_type}"
                )

            category.name = category_data.name
            base_slug = generate_slug(category_data.name)
            slug = base_slug

            counter = 1
            while True:
                existing = await session.execute(
                    select(Category).where(
                        parent_field == parent_id,
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

        await session.commit()
        await session.refresh(category)
        if category.submodality:
            await session.refresh(category, ["submodality"])
            await session.refresh(category.submodality, ["modality"])
        elif category.direct_modality:
            await session.refresh(category, ["direct_modality"])

        return CategoryResponse.from_orm(category)


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
