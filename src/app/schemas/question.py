from pydantic import BaseModel, Field, validator
from typing import Optional, List, Generic, TypeVar
from enum import Enum

T = TypeVar('T')


class ContextType(str, Enum):
    TEXT = "text"
    PDF = "pdf"


class QuestionStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DISABLED = "DISABLED"


class QuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=1, 
                               description="Texto de la pregunta")
    context_text: Optional[str] = Field(None, 
                                        description="Contexto en texto (requerido si context_type es 'text')")
    context_type: ContextType = Field(ContextType.TEXT, 
                                      description="Tipo de contexto: 'text' o 'pdf'")
    category_id: Optional[str] = Field(None, 
                                       description="ID de la categoría asociada")
    
    @validator('context_text')
    def validate_context_text(cls, v, values):
        if values.get('context_type') == ContextType.TEXT and not v:
            raise ValueError('context_text es requerido cuando context_type es "text"')
        return v


class QuestionApprovalRequest(BaseModel):
    action: str = Field(..., 
                        description="Acción a realizar: 'approve' o 'disable'")
    
    @validator('action')
    def validate_action(cls, v):
        if v not in ['approve', 'disable']:
            raise ValueError('action debe ser "approve" o "disable"')
        return v


class QuestionResponse(BaseModel):
    question_id: str
    status: str
    question_text: str
    context_type: str
    context_text: Optional[str] = None
    context_file: Optional[str] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    model_response: Optional[str] = None
    created_at: str


class PaginationInfo(BaseModel):
    """Información de paginación"""
    page: int = Field(..., description="Página actual (empezando en 1)")
    page_size: int = Field(..., description="Número de elementos por página")
    total_items: int = Field(..., description="Total de elementos")
    total_pages: int = Field(..., description="Total de páginas")
    has_next: bool = Field(..., description="Si hay página siguiente")
    has_previous: bool = Field(..., description="Si hay página anterior")


class PaginatedResponse(BaseModel, Generic[T]):
    """Respuesta paginada genérica"""
    items: List[T] = Field(..., description="Lista de elementos")
    pagination: PaginationInfo = Field(..., description="Información de paginación")


class PaginatedQuestionResponse(BaseModel):
    """Respuesta paginada específica para preguntas"""
    items: List[QuestionResponse] = Field(..., description="Lista de preguntas")
    pagination: PaginationInfo = Field(..., description="Información de paginación")
