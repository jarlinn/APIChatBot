"""
Controllers for Modalities
"""

from typing import List

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.app.db.session import get_async_session
from src.app.models import Modality, Submodality, Category
from src.app.schemas.modality import (
    ModalityCreate,
    ModalityUpdate,
    ModalityResponse,
    ModalityWithSubmodalities,
)
from src.app.dependencies.auth import get_current_active_user
from src.app.utils.string_utils import generate_slug

router = APIRouter(prefix="/modalities", tags=["modalities"])


@router.get("/", response_model=List[ModalityResponse])
async def get_modalities(
    skip: int = Query(0, ge=0, description="Number of elements to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of elements to return"
    ),
    current_user=Depends(get_current_active_user),
):
    """Get list of modalities"""
    async for session in get_async_session():
        query = select(Modality).options(
            selectinload(Modality.submodalities).selectinload(Submodality.categories).selectinload(Category.questions)
        )

        query = query.offset(skip).limit(limit).order_by(Modality.name)

        result = await session.execute(query)
        modalities = result.scalars().all()

        return [
            ModalityResponse(
                id=modality.id,
                name=modality.name,
                slug=modality.slug,
                description=modality.description,
                created_at=modality.created_at,
                updated_at=modality.updated_at,
                total_submodalities=modality.total_submodalities,
                total_categories=modality.total_categories,
                total_questions=modality.total_questions,
            )
            for modality in modalities
        ]


@router.get("/{modality_id}", response_model=ModalityWithSubmodalities)
async def get_modality(modality_id: str, current_user=Depends(get_current_active_user)):
    """Get a specific modality with its submodalities"""
    async for session in get_async_session():
        result = await session.execute(
            select(Modality)
            .where(Modality.id == modality_id)
            .options(
                selectinload(Modality.submodalities).selectinload(
                    Submodality.categories
                ).selectinload(Category.questions)
            )
        )
        modality = result.scalar_one_or_none()

        if not modality:
            raise HTTPException(status_code=404, detail="Modality not found")

        from src.app.schemas.submodality import SubmodalityResponse

        return ModalityWithSubmodalities(
            id=modality.id,
            name=modality.name,
            slug=modality.slug,
            description=modality.description,
            created_at=modality.created_at,
            updated_at=modality.updated_at,
            total_submodalities=modality.total_submodalities,
            total_categories=modality.total_categories,
            total_questions=modality.total_questions,
            submodalities=[
                SubmodalityResponse(
                    id=sub.id,
                    name=sub.name,
                    slug=sub.slug,
                    description=sub.description,
                    modality_id=sub.modality_id,
                    created_at=sub.created_at,
                    updated_at=sub.updated_at,
                    modality_name=modality.name,
                    full_name=sub.full_name,
                    full_path=sub.full_path,
                    total_categories=sub.total_categories,
                    total_questions=sub.total_questions,
                )
                for sub in modality.submodalities
            ],
        )


@router.post("/", response_model=ModalityResponse)
async def create_modality(
    modality_data: ModalityCreate, current_user=Depends(get_current_active_user)
):
    """Create a new modality"""
    async for session in get_async_session():
        # Check if modality with same name already exists
        existing_name = await session.execute(
            select(Modality).where(Modality.name == modality_data.name)
        )
        if existing_name.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail="Ya existe una modalidad con ese nombre"
            )

        base_slug = generate_slug(modality_data.name)
        slug = base_slug

        counter = 1
        while True:
            existing = await session.execute(
                select(Modality).where(Modality.slug == slug)
            )
            if not existing.scalar_one_or_none():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1

        modality = Modality(
            name=modality_data.name,
            slug=slug,
            description=modality_data.description,
        )

        session.add(modality)
        await session.commit()
        await session.refresh(modality)

        return ModalityResponse(
            id=modality.id,
            name=modality.name,
            slug=modality.slug,
            description=modality.description,
            created_at=modality.created_at,
            updated_at=modality.updated_at,
            total_submodalities=0,
            total_categories=0,
            total_questions=0,
        )


@router.put("/{modality_id}", response_model=ModalityResponse)
async def update_modality(
    modality_id: str,
    modality_data: ModalityUpdate,
    current_user=Depends(get_current_active_user),
):
    """Update a modality"""
    async for session in get_async_session():
        result = await session.execute(
            select(Modality)
            .where(Modality.id == modality_id)
            .options(
                selectinload(Modality.submodalities).selectinload(
                    Submodality.categories
                ).selectinload(Category.questions)
            )
        )
        modality = result.scalar_one_or_none()

        if not modality:
            raise HTTPException(status_code=404, detail="Modality not found")

        if modality_data.name is not None:
            # Check if another modality with same name already exists
            existing_name = await session.execute(
                select(Modality).where(
                    Modality.name == modality_data.name, Modality.id != modality_id
                )
            )
            if existing_name.scalar_one_or_none():
                raise HTTPException(
                    status_code=409,
                    detail="Ya existe otra modalidad con ese nombre"
                )

            modality.name = modality_data.name
            base_slug = generate_slug(modality_data.name)
            slug = base_slug

            counter = 1
            while True:
                existing = await session.execute(
                    select(Modality).where(
                        Modality.slug == slug, Modality.id != modality_id
                    )
                )
                if not existing.scalar_one_or_none():
                    break
                slug = f"{base_slug}-{counter}"
                counter += 1

            modality.slug = slug

        if modality_data.description is not None:
            modality.description = modality_data.description

        await session.commit()
        await session.refresh(modality)

        return ModalityResponse(
            id=modality.id,
            name=modality.name,
            slug=modality.slug,
            description=modality.description,
            created_at=modality.created_at,
            updated_at=modality.updated_at,
            total_submodalities=modality.total_submodalities,
            total_categories=modality.total_categories,
            total_questions=modality.total_questions,
        )


@router.delete("/{modality_id}")
async def delete_modality(
    modality_id: str, current_user=Depends(get_current_active_user)
):
    """Delete a modality (only if it has no submodalities)"""
    async for session in get_async_session():
        result = await session.execute(
            select(Modality)
            .where(Modality.id == modality_id)
            .options(selectinload(Modality.submodalities))
        )
        modality = result.scalar_one_or_none()

        if not modality:
            raise HTTPException(status_code=404, detail="Modality not found")

        if modality.submodalities:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete a modality that has submodalities",
            )

        await session.delete(modality)
        await session.commit()

        return {"message": "Modality deleted successfully"}
