"""
Custom error handlers for friendlier responses
"""

import logging
import re
from datetime import datetime
from typing import Optional

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.app.schemas.error import (
    ErrorResponse, 
    ValidationErrorResponse, 
    ValidationErrorDetail, 
    CustomHTTPException, 
    ErrorDetail
)

logger = logging.getLogger(__name__)


def validate_email_format(email: str) -> tuple[bool, str]:
    """
    Validate email format and return (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, "El email es requerido"

    email = email.strip()

    # Basic regex for email validation (RFC 5322 compliant)
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(email_regex, email):
        return False, "El formato del email no es válido. Debe ser algo como: usuario@dominio.com"

    # Check for problematic domains
    domain = email.split('@')[1].lower()
    if domain in ['localhost', 'example.com', 'test.com'] or domain.endswith('.local'):
        return False, f"El dominio '{domain}' no es válido. Usa un dominio real como gmail.com, outlook.com, etc."

    return True, ""


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Pydantic's custom validation error handler
    Turns technical errors into user-friendly messages
    """

    validation_errors = []

    for error in exc.errors():
        field = error.get("loc", [])[-1] if error.get("loc") else "campo"
        error_type = error.get("type", "")
        error_msg = error.get("msg", "")
        input_value = error.get("input", "")

        if "email" in str(field).lower():
            if "missing" in error_type:
                friendly_msg = "El email es requerido"
            elif "value_error" in error_type or "email" in error_type:
                # Use proper email validation
                is_valid, validation_msg = validate_email_format(str(input_value))
                if not is_valid:
                    friendly_msg = validation_msg
                else:
                    friendly_msg = "El formato del email no es válido"
            else:
                friendly_msg = f"Error en el email: {error_msg}"

        elif "password" in str(field).lower():
            if "missing" in error_type:
                friendly_msg = "La contraseña es requerida"
            elif "too_short" in error_type or ("string_too_short" in error_type and "6" in error_msg):
                friendly_msg = "La contraseña debe tener al menos 6 caracteres"
            else:
                # For other password errors, provide a generic message
                friendly_msg = "La contraseña no cumple con los requisitos de seguridad"

        else:
            # Para otros campos, usar mensaje genérico mejorado
            if "missing" in error_type:
                friendly_msg = f"El campo '{field}' es requerido"
            elif "type_error" in error_type:
                friendly_msg = f"El campo '{field}' tiene un tipo de dato incorrecto"
            else:
                friendly_msg = error_msg

        validation_errors.append(ValidationErrorDetail(
            field=field,
            message=friendly_msg,
            input_value=input_value if input_value else None
        ))

    logger.warning(f"Error de validación en {request.url}: {[e.dict() for e in validation_errors]}")

    response = ValidationErrorResponse(
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message="Datos de entrada inválidos. Por favor revisa los siguientes campos.",
            details={}
        ),
        timestamp=datetime.utcnow().isoformat() + 'Z',
        validation_errors=validation_errors
    )

    return JSONResponse(
        status_code=422,
        content=response.dict()
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Custom HTTP exception handler
    """

    friendly_messages = {
        400: "Solicitud incorrecta",
        401: "Credenciales inválidas o token expirado",
        403: "No tienes permisos para realizar esta acción",
        404: "Recurso no encontrado",
        409: "Conflicto - el recurso ya existe",
        422: "Datos de entrada inválidos",
        500: "Error interno del servidor"
    }

    friendly_msg = friendly_messages.get(exc.status_code, "Error en la solicitud")

    logger.warning(f"HTTP {exc.status_code} en {request.url}: {exc.detail}")

    response = ErrorResponse(
        error=ErrorDetail(
            code=f"HTTP_{exc.status_code}",
            message=friendly_msg,
            details={"original_detail": exc.detail, "status_code": exc.status_code}
        ),
        timestamp=datetime.utcnow().isoformat() + 'Z'
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response.dict()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for general errors not captured
    """

    logger.error(f"Error no manejado en {request.url}: {str(exc)}", exc_info=True)

    response = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_ERROR",
            message="Ocurrió un error inesperado. Por favor intenta de nuevo.",
            details={"exception_type": type(exc).__name__}
        ),
        timestamp=datetime.utcnow().isoformat() + 'Z'
    )

    return JSONResponse(
        status_code=500,
        content=response.dict()
    )


def create_error_response(
    message: str,
    details: Optional[str] = None,
    status_code: int = 400,
    error_code: Optional[str] = None
) -> JSONResponse:
    """
    Creates a consistent error response
    """
    content = {
        "error": message,
        "mensaje": details or message,
        "codigo": error_code or f"ERROR_{status_code}"
    }
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )

async def custom_http_exception_handler(request: Request, exc: CustomHTTPException) -> JSONResponse:
    """
    Custom HTTP exception handler
    """

    logger.warning(f"Custom HTTP {exc.status_code} en {request.url}: {exc.message}")

    response = ErrorResponse(
        error=ErrorDetail(
            code=exc.code,
            message=exc.message,
            details=exc.details
        ),
        timestamp=datetime.utcnow().isoformat() + 'Z'
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump()
    )

