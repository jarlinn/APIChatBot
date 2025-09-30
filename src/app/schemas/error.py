"""
Schemes for standardized error responses
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Error Detail model"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Error Response model"""
    success: bool = False
    error: ErrorDetail
    timestamp: str


class CustomHTTPException(Exception):
    """
    Custom exception for HTTP errors
    """

    def __init__(self, status_code: int, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationErrorDetail(BaseModel):
    """Validation Errore model"""
    field: str
    message: str
    input_value: Optional[Any] = None


class ValidationErrorResponse(BaseModel):
    """Validation Error Response model"""
    success: bool = False
    error: ErrorDetail
    timestamp: str
    validation_errors: list[ValidationErrorDetail]
