"""
Controller for Chatbot Configuration
"""
import logging
from typing import Optional
from sqlalchemy import select
from fastapi import APIRouter, HTTPException, Depends

from src.app.db.session import get_async_session
from src.app.models.chatbot_config import ChatbotConfig
from src.app.schemas.chatbot_config import (
    ChatbotConfigResponse,
    GreetingConfigResponse,
    GreetingConfigUpdate,
    ContactInfoResponse,
    ContactInfoUpdate,
    FormattedContactInfoResponse,
)
from src.app.dependencies.auth import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_or_create_config(session) -> ChatbotConfig:
    """
    Get the existing config or create a new one if it doesn't exist.
    This ensures there's always a single config instance (singleton pattern).
    """
    result = await session.execute(select(ChatbotConfig))
    config = result.scalar_one_or_none()
    
    if not config:
        # Create default config
        config = ChatbotConfig(
            greeting_message="¡Hola! Soy el asistente virtual de la UFPS. ¿En qué puedo ayudarte?",
            greeting_enabled=True,
        )
        session.add(config)
        await session.commit()
        await session.refresh(config)
        logger.info("Created default chatbot configuration")
    
    return config


# ============================================================================
# GREETING ENDPOINTS
# ============================================================================

@router.get("/config/greeting", response_model=GreetingConfigResponse)
async def get_greeting_config():
    """
    Get only the greeting configuration.
    This endpoint is public and doesn't require authentication.
    """
    async for session in get_async_session():
        config = await get_or_create_config(session)
        
        return GreetingConfigResponse(
            greeting_message=config.greeting_message,
            greeting_enabled=config.greeting_enabled,
        )


@router.patch("/config/greeting", response_model=GreetingConfigResponse)
async def update_greeting_config(
    update_data: GreetingConfigUpdate,
    current_user=Depends(get_current_active_user),
):
    """
    Update only the greeting configuration.
    Only updates the fields that are provided in the request.
    
    Requires authentication (admin only).
    """
    async for session in get_async_session():
        config = await get_or_create_config(session)
        
        # Update only the fields that are provided (not None)
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for field, value in update_dict.items():
            if value is not None:
                setattr(config, field, value)
        
        await session.commit()
        await session.refresh(config)
        
        logger.info(f"Greeting configuration updated by user {current_user.email}")
        logger.info(f"Updated fields: {list(update_dict.keys())}")
        
        return GreetingConfigResponse(
            greeting_message=config.greeting_message,
            greeting_enabled=config.greeting_enabled,
        )


# ============================================================================
# CONTACT INFO ENDPOINTS
# ============================================================================

@router.get("/config/contact", response_model=ContactInfoResponse)
async def get_contact_config():
    """
    Get only the contact information configuration.
    This endpoint is public and doesn't require authentication.
    """
    async for session in get_async_session():
        config = await get_or_create_config(session)
        
        return ContactInfoResponse(
            office_name=config.office_name,
            faculty_name=config.faculty_name,
            university_name=config.university_name,
            campus_location=config.campus_location,
            building_name=config.building_name,
            floor_office=config.floor_office,
            street_address=config.street_address,
            city=config.city,
            state=config.state,
            country=config.country,
            director_name=config.director_name,
            contact_phone=config.contact_phone,
            contact_email=config.contact_email,
            website_url=config.website_url,
            office_hours=config.office_hours,
            social_facebook=config.social_facebook,
            social_instagram=config.social_instagram,
            social_twitter=config.social_twitter,
            social_youtube=config.social_youtube,
            social_linkedin=config.social_linkedin,
            full_address=config.full_address,
            full_location=config.full_location,
        )


@router.get("/config/contact/formatted", response_model=FormattedContactInfoResponse)
async def get_formatted_contact_info():
    """
    Get formatted contact information as a beautiful string.
    This endpoint returns only the contact information in a formatted way,
    including social media links if available.
    
    This endpoint is public and doesn't require authentication.
    """
    async for session in get_async_session():
        config = await get_or_create_config(session)
        formatted_text = config.get_formatted_contact_info()
        
        return FormattedContactInfoResponse(formatted_text=formatted_text)


@router.patch("/config/contact", response_model=ContactInfoResponse)
async def update_contact_config(
    update_data: ContactInfoUpdate,
    current_user=Depends(get_current_active_user),
):
    """
    Update only the contact information configuration.
    Only updates the fields that are provided in the request.
    Fields not included in the request will keep their current values.
    
    Requires authentication (admin only).
    """
    async for session in get_async_session():
        config = await get_or_create_config(session)
        
        # Update only the fields that are provided (not None)
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for field, value in update_dict.items():
            if value is not None:
                setattr(config, field, value)
        
        await session.commit()
        await session.refresh(config)
        
        logger.info(f"Contact information updated by user {current_user.email}")
        logger.info(f"Updated fields: {list(update_dict.keys())}")
        
        return ContactInfoResponse(
            office_name=config.office_name,
            faculty_name=config.faculty_name,
            university_name=config.university_name,
            campus_location=config.campus_location,
            building_name=config.building_name,
            floor_office=config.floor_office,
            street_address=config.street_address,
            city=config.city,
            state=config.state,
            country=config.country,
            director_name=config.director_name,
            contact_phone=config.contact_phone,
            contact_email=config.contact_email,
            website_url=config.website_url,
            office_hours=config.office_hours,
            social_facebook=config.social_facebook,
            social_instagram=config.social_instagram,
            social_twitter=config.social_twitter,
            social_youtube=config.social_youtube,
            social_linkedin=config.social_linkedin,
            full_address=config.full_address,
            full_location=config.full_location,
        )


# ============================================================================
# COMPLETE CONFIG ENDPOINTS (for admin panel)
# ============================================================================

@router.get("/config", response_model=ChatbotConfigResponse)
async def get_chatbot_config():
    """
    Get the complete chatbot configuration (greeting + contact info).
    This endpoint is useful for admin panels that need all data at once.
    This endpoint is public and doesn't require authentication.
    """
    async for session in get_async_session():
        config = await get_or_create_config(session)
        
        return ChatbotConfigResponse(
            id=str(config.id),
            greeting_message=config.greeting_message,
            greeting_enabled=config.greeting_enabled,
            office_name=config.office_name,
            faculty_name=config.faculty_name,
            university_name=config.university_name,
            campus_location=config.campus_location,
            building_name=config.building_name,
            floor_office=config.floor_office,
            street_address=config.street_address,
            city=config.city,
            state=config.state,
            country=config.country,
            director_name=config.director_name,
            contact_phone=config.contact_phone,
            contact_email=config.contact_email,
            website_url=config.website_url,
            office_hours=config.office_hours,
            social_facebook=config.social_facebook,
            social_instagram=config.social_instagram,
            social_twitter=config.social_twitter,
            social_youtube=config.social_youtube,
            social_linkedin=config.social_linkedin,
            is_active=config.is_active,
            full_address=config.full_address,
            full_location=config.full_location,
            created_at=str(config.created_at),
            updated_at=str(config.updated_at) if config.updated_at else None,
        )


@router.post("/config/reset", response_model=ChatbotConfigResponse)
async def reset_chatbot_config(
    current_user=Depends(get_current_active_user),
):
    """
    Reset chatbot configuration to default values.
    This will clear all contact information and reset the greeting message.
    
    Requires authentication (admin only).
    """
    async for session in get_async_session():
        config = await get_or_create_config(session)
        
        # Reset to default values
        config.greeting_message = "¡Hola! Soy el asistente virtual de la UFPS. ¿En qué puedo ayudarte?"
        config.greeting_enabled = True
        config.office_name = None
        config.faculty_name = None
        config.university_name = None
        config.campus_location = None
        config.building_name = None
        config.floor_office = None
        config.street_address = None
        config.city = None
        config.state = None
        config.country = None
        config.director_name = None
        config.contact_phone = None
        config.contact_email = None
        config.website_url = None
        config.office_hours = None
        config.social_facebook = None
        config.social_instagram = None
        config.social_twitter = None
        config.social_youtube = None
        config.social_linkedin = None
        
        await session.commit()
        await session.refresh(config)
        
        logger.info(f"Chatbot configuration reset to defaults by user {current_user.email}")
        
        return ChatbotConfigResponse(
            id=str(config.id),
            greeting_message=config.greeting_message,
            greeting_enabled=config.greeting_enabled,
            office_name=config.office_name,
            faculty_name=config.faculty_name,
            university_name=config.university_name,
            campus_location=config.campus_location,
            building_name=config.building_name,
            floor_office=config.floor_office,
            street_address=config.street_address,
            city=config.city,
            state=config.state,
            country=config.country,
            contact_phone=config.contact_phone,
            contact_email=config.contact_email,
            website_url=config.website_url,
            office_hours=config.office_hours,
            social_facebook=config.social_facebook,
            social_instagram=config.social_instagram,
            social_twitter=config.social_twitter,
            social_youtube=config.social_youtube,
            social_linkedin=config.social_linkedin,
            is_active=config.is_active,
            full_address=config.full_address,
            full_location=config.full_location,
            created_at=str(config.created_at),
            updated_at=str(config.updated_at) if config.updated_at else None,
        )