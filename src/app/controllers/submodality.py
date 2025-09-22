"""
Controllers for Submodalities
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.app.db.session import get_async_session
from src.app.models import Modality, Submodality, Category
from src.app.schemas.submodality import (
    SubmodalityCreate,
    SubmodalityUpdate,
    SubmodalityResponse,
    SubmodalityWithCategories,
)
from src.app.dependencies.auth import get_current_active_user
from src.app.utils.string_utils import generate_slug

router = APIRouter(prefix="/submodalities", tags=["submodalities"])


@router.get("/", response_model=List[SubmodalityResponse])
async def get_submodalities(
    skip: int = Query(0, ge=0, description="Number of elements to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of elements to return"
    ),
    modality_id: Optional[str] = Query(None, description="Filter by modality"),
    current_user=Depends(get_current_active_user),
):
    """Get list of submodalities"""
    async for session in get_async_session():
        query = select(Submodality).options(
            selectinload(Submodality.modality),
            selectinload(Submodality.categories).selectinload(Category.questions)
        )

        if modality_id:
            query = query.where(Submodality.modality_id == modality_id)

        query = query.offset(skip).limit(limit).order_by(Submodality.name)

        result = await session.execute(query)
        submodalities = result.scalars().all()

        return [
            SubmodalityResponse(
                id=sub.id,
                name=sub.name,
                slug=sub.slug,
                description=sub.description,
                modality_id=sub.modality_id,
                created_at=sub.created_at,
                updated_at=sub.updated_at,
                modality_name=sub.modality.name if sub.modality else None,
                full_name=sub.full_name,
                full_path=sub.full_path,
                total_categories=sub.total_categories,
                total_questions=sub.total_questions,
            )
            for sub in submodalities
        ]


@router.get("/{submodality_id}", response_model=SubmodalityWithCategories)
async def get_submodality(
    submodality_id: str, current_user=Depends(get_current_active_user)
):
    """Get a specific submodality with its categories"""
    async for session in get_async_session():
        result = await session.execute(
            select(Submodality)
            .where(Submodality.id == submodality_id)
            .options(
                selectinload(Submodality.modality),
                selectinload(Submodality.categories).selectinload(Category.questions)
            )
        )
        submodality = result.scalar_one_or_none()

        if not submodality:
            raise HTTPException(status_code=404, detail="Submodality not found")

        from src.app.schemas.category import CategoryResponse

        return SubmodalityWithCategories(
            id=submodality.id,
            name=submodality.name,
            slug=submodality.slug,
            description=submodality.description,
            modality_id=submodality.modality_id,
            created_at=submodality.created_at,
            updated_at=submodality.updated_at,
            modality_name=submodality.modality.name if submodality.modality else None,
            full_name=submodality.full_name,
            full_path=submodality.full_path,
            total_categories=submodality.total_categories,
            total_questions=submodality.total_questions,
            categories=[
                CategoryResponse(
                    id=cat.id,
                    name=cat.name,
                    slug=cat.slug,
                    description=cat.description,
                    submodality_id=cat.submodality_id,
                    created_at=cat.created_at,
                    updated_at=cat.updated_at,
                    submodality_name=submodality.name,
                    modality_name=(
                        submodality.modality.name if submodality.modality else None
                    ),
                    full_name=cat.full_name,
                    full_path=cat.full_path,
                    total_questions=cat.total_questions,
                )
                for cat in submodality.categories
            ],
        )


@router.post("/", response_model=SubmodalityResponse)
async def create_submodality(
    submodality_data: SubmodalityCreate, current_user=Depends(get_current_active_user)
):
    """Create a new submodality"""
    async for session in get_async_session():
        modality = await session.get(Modality, submodality_data.modality_id)
        if not modality:
            raise HTTPException(status_code=404, detail="Modality not found")

        base_slug = generate_slug(submodality_data.name)
        slug = base_slug

        counter = 1
        while True:
            existing = await session.execute(
                select(Submodality).where(
                    Submodality.modality_id == submodality_data.modality_id,
                    Submodality.slug == slug,
                )
            )
            if not existing.scalar_one_or_none():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1

        submodality = Submodality(
            name=submodality_data.name,
            slug=slug,
            description=submodality_data.description,
            modality_id=submodality_data.modality_id,
        )

        session.add(submodality)
        await session.commit()
        await session.refresh(submodality)
        await session.refresh(submodality, ["modality"])

        return SubmodalityResponse(
            id=submodality.id,
            name=submodality.name,
            slug=submodality.slug,
            description=submodality.description,
            modality_id=submodality.modality_id,
            created_at=submodality.created_at,
            updated_at=submodality.updated_at,
            modality_name=modality.name,
            full_name=submodality.full_name,
            full_path=submodality.full_path,
            total_categories=0,
            total_questions=0,
        )


@router.put("/{submodality_id}", response_model=SubmodalityResponse)
async def update_submodality(
    submodality_id: str,
    submodality_data: SubmodalityUpdate,
    current_user=Depends(get_current_active_user),
):
    """Update a submodality"""
    async for session in get_async_session():
        result = await session.execute(
            select(Submodality)
            .where(Submodality.id == submodality_id)
            .options(
                selectinload(Submodality.modality),
                selectinload(Submodality.categories).selectinload(Category.questions)
            )
        )
        submodality = result.scalar_one_or_none()

        if not submodality:
            raise HTTPException(status_code=404, detail="Submodality not found")

        if (
            submodality_data.modality_id
            and submodality_data.modality_id != submodality.modality_id
        ):
            modality = await session.get(Modality, submodality_data.modality_id)
            if not modality:
                raise HTTPException(status_code=404, detail="Modality not found")

        if submodality_data.name is not None:
            submodality.name = submodality_data.name
            base_slug = generate_slug(submodality_data.name)
            slug = base_slug

            modality_id_to_check = (
                submodality_data.modality_id or submodality.modality_id
            )
            counter = 1
            while True:
                existing = await session.execute(
                    select(Submodality).where(
                        Submodality.modality_id == modality_id_to_check,
                        Submodality.slug == slug,
                        Submodality.id != submodality_id,
                    )
                )
                if not existing.scalar_one_or_none():
                    break
                slug = f"{base_slug}-{counter}"
                counter += 1

            submodality.slug = slug

        if submodality_data.description is not None:
            submodality.description = submodality_data.description
        if submodality_data.modality_id is not None:
            submodality.modality_id = submodality_data.modality_id

        await session.commit()
        await session.refresh(submodality)
        await session.refresh(submodality, ["modality"])

        return SubmodalityResponse(
            id=submodality.id,
            name=submodality.name,
            slug=submodality.slug,
            description=submodality.description,
            modality_id=submodality.modality_id,
            created_at=submodality.created_at,
            updated_at=submodality.updated_at,
            modality_name=submodality.modality.name if submodality.modality else None,
            full_name=submodality.full_name,
            full_path=submodality.full_path,
            total_categories=submodality.total_categories,
            total_questions=submodality.total_questions,
        )


@router.delete("/{submodality_id}")
async def delete_submodality(
    submodality_id: str, current_user=Depends(get_current_active_user)
):
    """Delete a submodality (only if it has no categories)"""
    async for session in get_async_session():
        result = await session.execute(
            select(Submodality)
            .where(Submodality.id == submodality_id)
            .options(selectinload(Submodality.categories).selectinload(Category.questions))
        )
        submodality = result.scalar_one_or_none()

        if not submodality:
            raise HTTPException(status_code=404, detail="Submodality not found")

        if submodality.categories:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete a submodality that has categories",
            )

        await session.delete(submodality)
        await session.commit()

        return {"message": "Submodality deleted successfully"}
