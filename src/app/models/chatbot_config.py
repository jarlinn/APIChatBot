"""
Model for Chatbot Configuration
"""
import uuid
from sqlalchemy import Column, String, Text, Boolean, TIMESTAMP
from sqlalchemy.sql import func
from ..db.database import Base


class ChatbotConfig(Base):
    """
    Model for Chatbot Configuration
    Stores greeting message and detailed contact information
    """
    __tablename__ = "chatbot_config"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Greeting Configuration
    greeting_message = Column(Text, nullable=False, 
                             default="¡Hola! Soy el asistente virtual de la UFPS. ¿En qué puedo ayudarte?")
    greeting_enabled = Column(Boolean, default=True)
    
    # Program/Office Information
    office_name = Column(String(255), nullable=True)
    faculty_name = Column(String(255), nullable=True)
    university_name = Column(String(255), nullable=True)
    
    # Location Details
    campus_location = Column(String(255), nullable=True)
    building_name = Column(String(255), nullable=True)
    floor_office = Column(String(100), nullable=True)
    
    # Address Information
    street_address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Contact Information
    director_name = Column(String(60), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    contact_email = Column(String(255), nullable=True)
    website_url = Column(String(255), nullable=True)
    
    # Business Hours
    office_hours = Column(Text, nullable=True)
    
    # Social Media Links
    social_facebook = Column(String(255), nullable=True)
    social_instagram = Column(String(255), nullable=True)
    social_twitter = Column(String(255), nullable=True)
    social_youtube = Column(String(255), nullable=True)
    social_linkedin = Column(String(255), nullable=True)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ChatbotConfig(id='{self.id}', office='{self.office_name}')>"
    
    @property
    def full_address(self):
        """Returns the complete formatted address"""
        parts = []
        if self.street_address:
            parts.append(self.street_address)
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts) if parts else None
    
    @property
    def full_location(self):
        """Returns the complete location within campus"""
        parts = []
        if self.campus_location:
            parts.append(self.campus_location)
        if self.building_name:
            parts.append(self.building_name)
        if self.floor_office:
            parts.append(self.floor_office)
        return ", ".join(parts) if parts else None
    
    def get_formatted_contact_info(self) -> str:
        """
        Returns formatted contact information with Markdown formatting
        Uses bold, italic, emojis and proper structure for better readability
        """
        lines = []
        
        # Office/Program Information with bold
        if self.office_name:
            lines.append(f"**{self.office_name}**")
        if self.faculty_name:
            lines.append(f"*{self.faculty_name}*")
        if self.university_name:
            lines.append(f"*{self.university_name}*")
        
        if lines:
            lines.append("")  # Empty line separator
        
        # Location with emoji and bold label
        if self.full_location:
            lines.append(f"📍 **Ubicación:** {self.full_location}")
            lines.append("")
        
        # Address with emoji and bold label
        if self.full_address:
            lines.append(f"🏢 **Dirección:** {self.full_address}")
            lines.append("")
        
        # Phone with emoji and bold label
        if self.director_name:
            lines.append(f"👤 **Director/a:** {self.director_name}")
            lines.append("")

        # Phone with emoji and bold label
        if self.contact_phone:
            lines.append(f"📞 **Teléfono:** {self.contact_phone}")
            lines.append("")
        
        # Email with emoji and bold label
        if self.contact_email:
            lines.append(f"📧 **Correo Electrónico:** {self.contact_email}")
            lines.append("")
        
        # Website with emoji and bold label
        if self.website_url:
            lines.append(f"🌐 **Página Web:** {self.website_url}")
            lines.append("")
        
        # Office Hours with emoji and bold label
        if self.office_hours:
            lines.append(f"🕐 **Horario de Atención:** {self.office_hours}")
            lines.append("")
        
        # Social Media with emojis and bold labels
        social_media = []
        if self.social_facebook:
            social_media.append(f"  • **Facebook:** {self.social_facebook}")
        if self.social_instagram:
            social_media.append(f"  • **Instagram:** {self.social_instagram}")
        if self.social_twitter:
            social_media.append(f"  • **Twitter:** {self.social_twitter}")
        if self.social_youtube:
            social_media.append(f"  • **YouTube:** {self.social_youtube}")
        if self.social_linkedin:
            social_media.append(f"  • **LinkedIn:** {self.social_linkedin}")
        
        if social_media:
            lines.append("🔗 **Redes Sociales:**")
            lines.extend(social_media)
        
        return "\n".join(lines).strip()