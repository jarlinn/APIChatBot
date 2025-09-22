"""
Manejadores de errores personalizados para respuestas más amigables
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Manejador personalizado para errores de validación de Pydantic
    Convierte los errores técnicos en mensajes amigables para el usuario
    """
    
    errors = []
    
    for error in exc.errors():
        field = error.get("loc", [])[-1] if error.get("loc") else "campo"
        error_type = error.get("type", "")
        error_msg = error.get("msg", "")
        input_value = error.get("input", "")
        
        # Mensajes personalizados según el tipo de error
        if "email" in str(field).lower():
            if "value_error" in error_type or "email" in error_type:
                # Mensajes específicos para emails inválidos
                if ".local" in str(input_value):
                    friendly_msg = f"El dominio '.local' no es válido. Usa un dominio real como gmail.com, outlook.com, etc."
                elif ".localhost" in str(input_value):
                    friendly_msg = f"El dominio '.localhost' no es válido. Usa un dominio real como gmail.com, outlook.com, etc."
                elif "@" not in str(input_value):
                    friendly_msg = "El email debe contener el símbolo '@'"
                elif "." not in str(input_value).split("@")[-1]:
                    friendly_msg = "El dominio debe contener al menos un punto (ej: gmail.com)"
                else:
                    friendly_msg = f"El email '{input_value}' no tiene un formato válido. Debe ser algo como: usuario@dominio.com"
            elif "missing" in error_type:
                friendly_msg = "El email es requerido"
            else:
                friendly_msg = f"Error en el email: {error_msg}"
        
        elif "password" in str(field).lower():
            if "missing" in error_type:
                friendly_msg = "La contraseña es requerida"
            elif "too_short" in error_type or "6 caracteres" in error_msg:
                friendly_msg = "La contraseña debe tener al menos 6 caracteres"
            elif "value_error" in error_type and "caracteres" in error_msg:
                friendly_msg = "La contraseña debe tener al menos 6 caracteres"
            else:
                # Limpiar el mensaje de error técnico
                clean_msg = error_msg.replace("Value error, ", "").replace("value error: ", "")
                friendly_msg = clean_msg
        
        else:
            # Para otros campos, usar mensaje genérico mejorado
            if "missing" in error_type:
                friendly_msg = f"El campo '{field}' es requerido"
            elif "type_error" in error_type:
                friendly_msg = f"El campo '{field}' tiene un tipo de dato incorrecto"
            else:
                friendly_msg = error_msg
        
        errors.append({
            "campo": field,
            "mensaje": friendly_msg,
            "valor_recibido": input_value if input_value else None
        })
    
    # Log del error para debugging
    logger.warning(f"Error de validación en {request.url}: {errors}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Datos de entrada inválidos",
            "mensaje": "Por favor revisa los siguientes campos:",
            "detalles": errors,
            "codigo": "VALIDATION_ERROR"
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Manejador personalizado para excepciones HTTP
    """
    
    # Mensajes personalizados según el código de estado
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
    
    # Log del error
    logger.warning(f"HTTP {exc.status_code} en {request.url}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": friendly_msg,
            "mensaje": exc.detail,
            "codigo": f"HTTP_{exc.status_code}",
            "status_code": exc.status_code
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    Manejador para errores generales no capturados
    """
    
    logger.error(f"Error no manejado en {request.url}: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Error interno del servidor",
            "mensaje": "Ocurrió un error inesperado. Por favor intenta de nuevo.",
            "codigo": "INTERNAL_ERROR"
        }
    )


# Función helper para crear respuestas de error consistentes
def create_error_response(
    message: str,
    details: str = None,
    status_code: int = 400,
    error_code: str = None
):
    """
    Crea una respuesta de error consistente
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
