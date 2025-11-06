"""
Schemas for Chatbot Configuration
"""
from typing import Optional
from pydantic import BaseModel, EmailStr


class ChatbotConfigBase(BaseModel):
    """Base schema for chatbot configuration"""
    # Greeting
    greeting_message: str
    greeting_enabled: bool = True
    
    # Program/Office Information
    office_name: Optional[str] = None
    faculty_name: Optional[str] = None
    university_name: Optional[str] = None
    
    # Location Details
    campus_location: Optional[str] = None
    building_name: Optional[str] = None
    floor_office: Optional[str] = None
    
    # Address Information
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    
    # Contact Information
    director_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    website_url: Optional[str] = None
    office_hours: Optional[str] = None
    
    # Social Media
    social_facebook: Optional[str] = None
    social_instagram: Optional[str] = None
    social_twitter: Optional[str] = None
    social_youtube: Optional[str] = None
    social_linkedin: Optional[str] = None


class GreetingConfigUpdate(BaseModel):
    """Schema for updating only greeting configuration"""
    greeting_message: Optional[str] = None
    greeting_enabled: Optional[bool] = None


class ContactInfoUpdate(BaseModel):
    """Schema for updating only contact information"""
    office_name: Optional[str] = None
    faculty_name: Optional[str] = None
    university_name: Optional[str] = None
    campus_location: Optional[str] = None
    building_name: Optional[str] = None
    floor_office: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    director_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    website_url: Optional[str] = None
    office_hours: Optional[str] = None
    social_facebook: Optional[str] = None
    social_instagram: Optional[str] = None
    social_twitter: Optional[str] = None
    social_youtube: Optional[str] = None
    social_linkedin: Optional[str] = None


class ChatbotConfigUpdate(BaseModel):
    """Schema for updating chatbot configuration (all fields optional)"""
    greeting_message: Optional[str] = None
    greeting_enabled: Optional[bool] = None
    office_name: Optional[str] = None
    faculty_name: Optional[str] = None
    university_name: Optional[str] = None
    campus_location: Optional[str] = None
    building_name: Optional[str] = None
    floor_office: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    director_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    website_url: Optional[str] = None
    office_hours: Optional[str] = None
    social_facebook: Optional[str] = None
    social_instagram: Optional[str] = None
    social_twitter: Optional[str] = None
    social_youtube: Optional[str] = None
    social_linkedin: Optional[str] = None


class GreetingConfigResponse(BaseModel):
    """Schema for greeting configuration response"""
    greeting_message: str
    greeting_enabled: bool
    
    class Config:
        from_attributes = True


class ContactInfoResponse(BaseModel):
    """Schema for contact information response"""
    office_name: Optional[str] = None
    faculty_name: Optional[str] = None
    university_name: Optional[str] = None
    campus_location: Optional[str] = None
    building_name: Optional[str] = None
    floor_office: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    director_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    website_url: Optional[str] = None
    office_hours: Optional[str] = None
    social_facebook: Optional[str] = None
    social_instagram: Optional[str] = None
    social_twitter: Optional[str] = None
    social_youtube: Optional[str] = None
    social_linkedin: Optional[str] = None
    full_address: Optional[str] = None
    full_location: Optional[str] = None
    
    class Config:
        from_attributes = True


class ChatbotConfigResponse(ChatbotConfigBase):
    """Schema for chatbot configuration response"""
    id: str
    is_active: bool
    full_address: Optional[str] = None
    full_location: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class FormattedContactInfoResponse(BaseModel):
    """Schema for formatted contact information response as text"""
    formatted_text: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "formatted_text": (
                    "Oficina Administrativa del Programa de Ingeniería de Sistemas\n"
                    "Facultad de Ingeniería\n"
                    "Universidad Francisco de Paula Santander\n\n"
                    "Ubicación: Campus Central, Edificio de Ingenierías, Piso 2.\n\n"
                    "Dirección: Av. Gran Colombia No. 12E-96, Cúcuta, Norte de Santander, Colombia.\n\n"
                    "Teléfono: +57 (7) 5776655\n\n"
                    "Correo Electrónico: oficina.sistemas@ufps.edu.co\n\n"
                    "Página Web: www.ufps.edu.co/ingenieria/sistemas\n\n"
                    "Horario de Atención: Lunes a Viernes de 8:00 a.m. a 12:00 m. y de 2:00 p.m. a 5:00 p.m.\n\n"
                    "Redes Sociales:\n"
                    "  - Facebook: https://facebook.com/ufps\n"
                    "  - Instagram: https://instagram.com/ufps_oficial"
                )
            }
        }